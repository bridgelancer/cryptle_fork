"""This module maps enums to IB API mnemonics or POD."""

from datetime import date, timedelta
from enum import Enum

from tcalendar import need_rollover

from .contract import Contract



ASSET_CONTRACT_MAP = {}


_ = Contract()
_.symbol = 'HSI'
_.secType = 'FUT'
_.exchange = 'HKFE'
_.currency = 'HKD'

if need_rollover(date.today()):
    _.lastTradeDateOrContractMonth = (date.today() + timedelta(days=30)).strftime('%Y%m')
else:
    _.lastTradeDateOrContractMonth = date.today().strftime('%Y%m')
_.conid = 369009605

ASSET_CONTRACT_MAP['hsihkd'] = _


_ = Contract()
_.symbol = 'USD'
_.secType = 'CASH'
_.exchange = 'IDEALPRO'
_.currency = 'CNH'

ASSET_CONTRACT_MAP['usdcnh'] = _


_ = Contract()
_.symbol = 'TSLA'
_.secType = 'STK'
_.exchange = 'SMART'
_.currency = 'USD'

ASSET_CONTRACT_MAP['tslausd'] = _

_ = Contract()
_.symbol = 'USD'
_.secType = 'CASH'
_.exchange = 'IDEALPRO'
_.currency = 'CHF'

ASSET_CONTRACT_MAP['usdchf'] = _


OrderStatus = Enum(
    'OrderStatus',
    {
        'API_PENDING': 'ApiPending',
        'API_CANCELLED': 'ApiCancelled',
        'PENDING_SUBMIT': 'PendingSubmit',
        'PENDING_CANCEL': 'PendingCancel',
        'PRE_SUBMITTED': 'PreSubmitted',
        'SUBMITTED': 'Submitted',
        'CANCELLED': 'Cancelled',
        'FILLED': 'Filled',
        'INACTIVE': 'Inactive',
    },
)


OrderType = Enum(
    'OrderType',
    {
        'AUCTION': 'AUC',
        'MARKET': 'MKT',
        'MARKET_ON_CLOSE': 'MOC',
        'LIMIT': 'LMT',
        'LIMIT_ON_CLOSE': 'LOC',
        'STOP': 'STP',
        'STOP_LIMIT': 'STP LMT',
        'TRAILING_STOP': 'TRAIL',
        'TRAILING_LIMIT': 'TRAIL LIMIT',
        'VOLATILITY': 'VOL',
    },
)


# List of all callback methods of EWrapper
TWSEvent = Enum(
    'TWSEvent',
    [
        'connectAck',
        'marketDataType',
        'tickPrice',
        'tickSize',
        'tickSnapshotEnd',
        'tickGeneric',
        'tickString',
        'tickEFP',
        'orderStatus',
        'openOrder',
        'openOrderEnd',
        'connectionClosed',
        'updateAccountValue',
        'updatePortfolio',
        'updateAccountTime',
        'accountDownloadEnd',
        'nextValidId',
        'contractDetails',
        'bondContractDetails',
        'contractDetailsEnd',
        'execDetails',
        'execDetailsEnd',
        'updateMktDepth',
        'updateMktDepthL2',
        'updateNewsBulletin',
        'managedAccounts',
        'receiveFA',
        'historicalData',
        'historicalDataEnd',
        'scannerParameters',
        'scannerData',
        'scannerDataEnd',
        'realtimeBar',
        'currentTime',
        'fundamentalData',
        'deltaNeutralValidation',
        'commissionReport',
        'position',
        'positionEnd',
        'accountSummary',
        'accountSummaryEnd',
        'verifyMessageAPI',
        'verifyCompleted',
        'verifyAndAuthMessageAPI',
        'verifyAndAuthCompleted',
        'displayGroupList',
        'displayGroupUpdated',
        'positionMulti',
        'positionMultiEnd',
        'accountUpdateMulti',
        'accountUpdateMultiEnd',
        'tickOptionComputation',
        'securityDefinitionOptionParameter',
        'securityDefinitionOptionParameterEnd',
        'softDollarTiers',
        'familyCodes',
        'symbolSamples',
        'mktDepthExchanges',
        'tickNews',
        'smartComponents',
        'tickReqParams',
        'newsProviders',
        'newsArticle',
        'historicalNews',
        'historicalNewsEnd',
        'headTimestamp',
        'histogramData',
        'historicalDataUpdate',
        'rerouteMktDataReq',
        'rerouteMktDepthReq',
        'marketRule',
        'pnl',
        'pnlSingle',
        'historicalTicks',
        'historicalTicksBidAsk',
        'historicalTicksLast',
        'tickByTickAllLast',
        'tickByTickBidAsk',
        'tickByTickMidPoint',
    ],
)
