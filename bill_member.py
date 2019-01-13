from load_readings import get_readings
from datetime import datetime
import calendar
from tariff import BULB_TARIFF
from typing import Tuple


def calc_bill_for_account(account_history: list, bill_date: datetime) -> float:
    """
    Calculate bill for one account, only for electricity
    :param account_history: list with history of meter readings (readingDate, cumulative)
    :param bill_date: bill date, assumed that the billing date is the last day of the month
    :return: bill for bill date (for one month)
    """

    previous_month_reading = None
    current_month_reading = None
    next_month_reading = None

    # Get periods
    for reading in account_history:
        datetime_str = reading['readingDate'].split('T')[0]
        dt = datetime.strptime(datetime_str, '%Y-%m-%d')
        if dt.month == bill_date.month and dt.year == bill_date.year:
            current_month_reading = reading
            current_month_reading['date'] = dt
        if bill_date.month != 1 and dt.month == bill_date.month - 1 and dt.year == bill_date.year or \
                bill_date.month == 1 and dt.month == 12 and dt.year == bill_date.year - 1:
            previous_month_reading = reading
            previous_month_reading['date'] = dt
        if bill_date.month != 12 and dt.month == bill_date.month + 1 and dt.year == bill_date.year or \
                bill_date.month == 12 and dt.month == 1 and dt.year == bill_date.year + 1:
            next_month_reading = reading
            next_month_reading['date'] = dt

    if not all([previous_month_reading, current_month_reading, next_month_reading]):
        return -1

    # Calculate bill
    days_in_current_month = calendar.monthrange(current_month_reading['date'].year,
                                                current_month_reading['date'].month)[1]
    days_in_previous_month = calendar.monthrange(previous_month_reading['date'].year,
                                                 previous_month_reading['date'].month)[1]

    first_period_kwh = current_month_reading['cumulative'] - previous_month_reading['cumulative']
    second_period_kwh = next_month_reading['cumulative'] - current_month_reading['cumulative']

    days_in_first_period = current_month_reading['date'].day
    days_in_second_period = days_in_current_month - current_month_reading['date'].day

    days_in_first_period_total = days_in_previous_month - previous_month_reading['date'].day + \
        current_month_reading['date'].day
    days_in_second_period_total = days_in_current_month - current_month_reading['date'].day + \
        next_month_reading['date'].day

    bill = days_in_first_period * first_period_kwh / days_in_first_period_total + \
        days_in_second_period * second_period_kwh / days_in_second_period_total

    return bill


def calculate_bill(member_id: str, bill_date: str, account_id='ALL') -> Tuple[float, float]:
    """
    Calculate bill for member
    :param member_id: id of member
    :param account_id: id of account or ALL if need bill for all acounts
    :param bill_date: bill date, assumed that the billing date is the last day of the month
    :return: amount in £ and kWh
    """

    bill_date = datetime.strptime(bill_date, '%Y-%m-%d')
    data = get_readings()

    if member_id not in data:
        print('We have no data for {member_id} member id'.format(member_id=member_id))
        return -1, -1

    account_ids = [list(x.keys())[0] for x in data[member_id]]
    if account_id not in account_ids and account_id != 'ALL':
        print("we don't have {account_id} account id for {member_id} member id".format(
            account_id=account_id,
            member_id=member_id))
        return -1, -1

    kwh = 0
    if account_id == 'ALL':
        for account in account_ids:
            account_bill = calc_bill_for_account(data[member_id][0][account][0]['electricity'], bill_date)
            if account_bill == -1:
                print('Not enough data for getting bill')
                return -1, -1
            kwh += account_bill
    else:
        kwh = calc_bill_for_account(data[member_id][0][account_id][0]['electricity'], bill_date)

    amount = kwh * BULB_TARIFF["electricity"]["unit_rate"] / 100 + bill_date.day * BULB_TARIFF["electricity"][
        "standing_charge"] / 100

    return round(amount, 2), round(kwh)


def calculate_and_print_bill(member_id, account, bill_date):
    """Calculate the bill and then print it to screen.
    Account is an optional argument - I could bill for one account or many.
    There's no need to refactor this function."""
    member_id = member_id or 'member-123'
    bill_date = bill_date or '2017-08-31'
    account = account or 'ALL'
    amount, kwh = calculate_bill(member_id, bill_date, account)
    print('Hello {member}!'.format(member=member_id))
    print('Your bill for {account} on {date} is £{amount}'.format(
        account=account,
        date=bill_date,
        amount=amount))
    print('based on {kwh}kWh of usage in the last month'.format(kwh=kwh))
