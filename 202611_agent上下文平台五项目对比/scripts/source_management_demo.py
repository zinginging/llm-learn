"""Recovered offline adaptation/registry/recipe demo. No source connection or UI."""
import copy
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ContractError(ValueError):
    pass


def require(ok, message):
    if not ok:
        raise ContractError(message)


def cents(value):
    require(isinstance(value,str),'decimal string required')
    try:
        n = Decimal(value) * 100
    except InvalidOperation as e:
        raise ContractError('invalid decimal') from e
    require(n.is_finite() and n == n.to_integral_value(),'fractional/nonfinite cents')
    return int(n)


def normalize(binding, payload, tenant):
    require(binding['state']=='published','not published')
    require(binding['schema']==payload['schema'],'schema revision drift')
    require(binding['canonical']=='order-net@1','business model drift')
    kind = binding['kind']
    require(kind in ('sql','rest','hbase'),'unsupported adapter')
    try:
        if kind=='sql':
            rows = payload['rows']
            require(all(type(r['paid']) is int and type(r['refund']) is int for r in rows),'integer cents required')
            out = [(str(r['id']),r['tenant'],r['paid']-r['refund'],r['currency']) for r in rows]
        elif kind=='rest':
            require(payload['complete'] is True,'incomplete pagination')
            out = [(str(r['orderId']),r['tenantCode'],cents(r['payment']['paidYuan'])-cents(r['payment']['refundYuan']),r['payment']['currency']) for r in payload['data']['orders']]
        else:
            out=[]
            for row in payload['rows']:
                t, oid = row['rowkey'].split('|')
                cells=row['cells']
                out.append((oid,t,int(cells['pay:paid_fen'])-int(cells['pay:refund_fen']),cells['pay:currency']))
    except (KeyError,TypeError,ValueError) as e:
        raise ContractError('invalid source contract') from e
    require(all(r[1]==tenant and r[3]=='CNY' and r[0] for r in out),'scope/currency/identity invalid')
    require(len({r[0] for r in out})==len(out),'duplicate identity')
    return sorted(out)


def choose(bindings):
    for b in bindings:
        if b['state']=='published' and b['health']=='ready':
            require(b['asset']=='sales.orders' and b['canonical']=='order-net@1','fallback semantics mismatch')
            return b
    raise ContractError('no approved binding')


def compose(rows, optional=None):
    require(rows is not None,'required result unavailable')
    return {'metric':'net_receipts','metric_version':'v1','value_cents':sum(r[2] for r in rows),
            'currency':'CNY','status':'complete' if optional is not None else 'partial',
            'missing_optional':[] if optional is not None else ['notes']}


def fail(call):
    try:
        call()
    except ContractError:
        return
    raise AssertionError('expected contract rejection')


def run():
    bindings=[{'id':k,'kind':k,'schema':k+'-v1','asset':'sales.orders','canonical':'order-net@1',
               'state':'published','health':'ready','secret_ref':'secret://test/'+k} for k in ('sql','rest','hbase')]
    payloads={
      'sql':{'schema':'sql-v1','rows':[{'id':1,'tenant':'A','paid':10000,'refund':0,'currency':'CNY'}, {'id':2,'tenant':'A','paid':20000,'refund':5000,'currency':'CNY'}]},
      'rest':{'schema':'rest-v1','complete':True,'data':{'orders':[{'orderId':str(i),'tenantCode':'A','payment':{'paidYuan':p,'refundYuan':r,'currency':'CNY'}} for i,p,r in [(1,'100.00','0'),(2,'200.00','50.00')]]}},
      'hbase':{'schema':'hbase-v1','rows':[{'rowkey':'A|'+str(i),'cells':{'pay:paid_fen':p,'pay:refund_fen':r,'pay:currency':'CNY'}} for i,p,r in [(1,'10000','0'),(2,'20000','5000')]]}}
    outputs=[normalize(b,payloads[b['kind']],'A') for b in bindings]
    assert outputs[0]==outputs[1]==outputs[2]
    selected=choose(bindings)
    bundle=compose(outputs[0])
    assert bundle['value_cents']==25000 and bundle['status']=='partial'
    assert sum(compose(o)['value_cents'] for o in outputs)==75000
    assert compose([],optional=[])['value_cents']==0
    fail(lambda: compose(None))
    fail(lambda: normalize({**bindings[0],'state':'draft'},payloads['sql'],'A'))
    fail(lambda: normalize(bindings[0],{**payloads['sql'],'schema':'v2'},'A'))
    fail(lambda: normalize(bindings[0],payloads['sql'],'B'))
    fail(lambda: normalize({**bindings[0],'kind':'unknown'},payloads['sql'],'A'))
    fail(lambda: normalize(bindings[1],{**payloads['rest'],'complete':False},'A'))
    fail(lambda: cents('NaN'))
    fail(lambda: cents('0.001'))
    missing=copy.deepcopy(payloads['rest']);del missing['data']['orders'][0]['payment']['refundYuan']
    fail(lambda: normalize(bindings[1],missing,'A'))
    fallback=copy.deepcopy(bindings);fallback[0]['health']='down'
    assert choose(fallback)['id']=='rest'
    fallback[1]['canonical']='gross@1';fail(lambda: choose(fallback))
    report={'checked_at':'2026-11-17','scope':'重建后自建原型，无真实来源/UI/框架',
            'bindings':bindings,'canonical_records':outputs[0],'selected':selected['id'],'context_bundle':bundle,
            'incorrect_replica_total_cents':75000,'checks':'格式等价、发布/Schema/权限/金额/分页/回退/必需项检查通过'}
    (ROOT/'intermediate/接入管理原型结果.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('PASS: SQL/REST/HBase fixtures -> same records; 250 CNY, wrong replica sum 750')


if __name__=='__main__':
    run()
