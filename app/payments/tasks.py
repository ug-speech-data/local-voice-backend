from decimal import Decimal
import logging
from time import sleep

from celery import shared_task
from requests.exceptions import ConnectTimeout
from django.db import transaction as db_transaction

from accounts.models import User, Wallet
from dashboard.models import Audio, Participant
from local_voice.utils.constants import (ParticipantType, TransactionDirection,
                                         TransactionStatus,
                                         TransactionStatusMessages,
                                         ValidationStatus)
from payments.models import Transaction
from payments.third_parties.payhub import PayHub
from payments.third_parties.payhub_status_codes import PayHubStatusCodes
from setup.models import AppConfiguration

payhub = PayHub()
logger = logging.getLogger("django")


@shared_task()
@db_transaction.atomic()
def execute_transaction(transaction_id, callback_url) -> None:
    logger.info("Executing transaction {}".format(transaction_id))
    if not transaction_id:
        logger.info(f"Cannot execute a transaction with id: {transaction_id}")
        return

    transaction = Transaction.objects.select_for_update().filter(
        transaction_id=transaction_id).first()
    if transaction.success():
        logger.info("Transaction {} is successful".format(transaction_id))
        return

    amount = transaction.amount
    mobile = transaction.phone_number
    network = transaction.network.upper()[:3]

    if not (amount and mobile and network):
        logger.info(f"Transaction is not executable: {transaction_id}")
        return

    try:
        if transaction.direction == TransactionDirection.IN.value:
            response = payhub.collections(amount, mobile, network,
                                          transaction_id, callback_url)
        elif transaction.direction == TransactionDirection.OUT.value:
            response = payhub.disbursement(amount, mobile, network,
                                           transaction_id, callback_url)
    except ConnectTimeout as e:
        transaction.response_data = "Error in execute_collection_transaction: {}".format(
            e)
        logger.error("Error in execute_collection_transaction: {}".format(e))
        transaction.save()
        return
    except Exception as e:
        transaction.response_data = "Unknown error occurred."
        logger.error("Unknown error occurred.")
        return

    if not hasattr(response, "json"):
        logger.error("Error in execute_transaction: {}".format(response.text))
        return

    transaction.accepted_by_provider = True
    transaction.response_data = response.text
    transaction.save()

    status_code = response.json().get("status_code")
    if status_code == PayHubStatusCodes.PENDING.value or status_code == PayHubStatusCodes.DUPLICATE_TRANSACTION.value:
        transaction.status = TransactionStatus.PENDING.value
        transaction.status_message = TransactionStatusMessages.PENDING.value
        transaction.save()
        check_transaction_status(transaction_id)
    elif status_code == PayHubStatusCodes.FAILED.value:
        transaction.status = TransactionStatus.FAILED.value
        transaction.status_message = TransactionStatusMessages.FAILED.value
        transaction.save()
    elif status_code == PayHubStatusCodes.SUCCESS.value:
        transaction.status = TransactionStatus.SUCCESS.value
        transaction.status_message = TransactionStatusMessages.SUCCESS.value
        transaction.save()
        transaction.update_wallet_balances()

        # If the transaction is for a participant
        if hasattr(transaction, "participant"):
            participant = transaction.participant
            participant.paid = True
            participant.save()

    # Save to update participants
    if hasattr(transaction, "participants"):
        for participant in transaction.participants.all():
            participant.save()

    logger.error("Transaction {} status: {}".format(transaction_id,
                                                    response.text))


@shared_task()
def bulk_check_transaction_status(ids):
    transactions = Transaction.objects.filter(id__in=ids)
    for transaction in transactions:
        try:
            if not transaction.accepted_by_provider:
                # This transaction has not been executed yet.
                execute_transaction(transaction.transaction_id, None)
            else:
                check_transaction_status(
                    transaction.transaction_id, rounds=1, wait=0)
        except Exception as e:
            logger.error(str(e))
            continue


@shared_task()
@db_transaction.atomic()
def check_transaction_status(transaction_id, rounds=5, wait=5):
    if rounds <= 0:
        return
    sleep(wait)
    logger.info("Checking transaction {}".format(transaction_id))
    if not transaction_id:
        return

    transaction = Transaction.objects.select_for_update().filter(
        transaction_id=transaction_id).first()
    response = payhub.status_check(transaction_id)
    transaction.response_data = response.json()
    if response.json().get("status_code") == PayHubStatusCodes.PENDING.value:
        check_transaction_status(transaction_id, rounds - 1, wait * 2)
    elif response.json().get("status_code") == PayHubStatusCodes.FAILED.value:
        transaction.status = TransactionStatus.FAILED.value
        transaction.status_message = TransactionStatusMessages.FAILED.value
        transaction.save()
    elif response.json().get("status_code") == PayHubStatusCodes.SUCCESS.value:
        transaction.status = TransactionStatus.SUCCESS.value
        transaction.status_message = TransactionStatusMessages.SUCCESS.value
        transaction.save()
        transaction.update_wallet_balances()

        # If the transaction is for a participant
        if hasattr(transaction, "participant"):
            participant = transaction.participant
            participant.paid = True
            participant.save()

    transaction.save()

    # Save to update participants
    if hasattr(transaction, "participants"):
        for participant in transaction.participants.all():
            participant.save()
    print("Transaction {} status: {}".format(transaction_id,
                                             transaction.status_message))


@shared_task()
@db_transaction.atomic()
def update_participants_amount():
    configuration = AppConfiguration.objects.first()
    amount = configuration.individual_audio_aggregators_amount_per_audio if configuration else 0
    for participant in Participant.objects.select_for_update().filter(flatten=False, paid=False):
        if participant.type == ParticipantType.ASSISTED.value:
            amount = configuration.participant_amount_per_audio if configuration else 0
        participant.update_amount(amount)


@shared_task()
@db_transaction.atomic()
def update_user_amounts():
    configuration = AppConfiguration.objects.first()
    amount = configuration.audio_aggregators_amount_per_audio if configuration else 0
    amount_per_audio_validation = configuration.amount_per_audio_validation if configuration else 0
    TRANSCRIPTION_RATE = 0.7
    # dagbfh
    for user in User.objects.filter(deleted=False, is_active=True):
        user_audios = user.audios.filter(
            deleted=False,
            second_audio_status=ValidationStatus.ACCEPTED.value,
            participant__type=ParticipantType.ASSISTED.value).count()
        participant_audios = 0
        email_prefix = user.email_address.split("@")[0]
        if ("ugspeechdata.com" in user.email_address
                # Is not a lead
                and email_prefix[-2:].isdigit()
                # Is not a participant recruited by an enumerator
                and not email_prefix[-4:].isdigit()):

            users_participants = User.objects.filter(
                email_address__istartswith=email_prefix).exclude(
                    email_address=user.email_address)

            participant_audios = Audio.objects.filter(
                participant__type=ParticipantType.INDEPENDENT.value,
                second_audio_status=ValidationStatus.ACCEPTED.value,
                deleted=False,
                submitted_by__in=users_participants).count()

            user.accepted_audios_from_recruits = participant_audios
            user.save()

        audios_amount = amount * user_audios

        validations = Audio.objects.filter(validations__user=user).count()
        validations_amount = validations * amount_per_audio_validation

        transcription_amount = Decimal(
            (user.audios_transcribed + user.transcriptions_resolved) * TRANSCRIPTION_RATE)
        amount_accrued_by_recruits = Decimal(participant_audios * 0.2)

        wallet = Wallet.objects.select_for_update().get(
            id=user.wallet.id) or Wallet.objects.create()
        wallet.set_validation_benefit(validations_amount)
        wallet.set_recording_benefit(audios_amount)
        wallet.set_audios_by_recruits_benefit(amount_accrued_by_recruits)
        wallet.set_transcription_benefit(transcription_amount)

        # Calculate total direct deposits
        deposit_transactions = Transaction.objects.filter(
            wallet=wallet,
            status=TransactionStatus.SUCCESS.value,
            direction=TransactionDirection.IN.value,
            amount__gt=0,
            note="DIRECT DEPOSIT").values_list("amount", flat=True)
        total_deposits = sum(deposit_transactions)
        total_accrued_amount = total_deposits + audios_amount + \
            validations_amount + transcription_amount + amount_accrued_by_recruits
        wallet.set_accrued_amount(total_accrued_amount)
