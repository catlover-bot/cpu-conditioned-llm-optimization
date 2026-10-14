# Exact parser function projection from original GPU005 source; no deployment/bootstrap.
def response_text(provider,obj,cfg):
    if provider=='qwen':
        P.require(obj.get('truncated') is False and obj.get('stop_type') in ('eos','word'),'Qwen incomplete output')
        n=obj.get('timings',{}).get('predicted_n');cap=cfg['models']['qwen']['max_output_tokens']
        P.require(type(n) is int and 0<n<=cap+8,'Invalid Qwen token count');return obj.get('content')
    need(obj.get('model')==cfg['models'][provider]['id'],'Recorded model differs')
    if provider=='openai':
        P.require(obj.get('status')=='completed' and not obj.get('error'),'OpenAI incomplete/refused/failed response')
        pieces=[]
        for item in obj.get('output',[]):
            if item.get('type')=='reasoning':continue
            P.require(item.get('type')=='message' and item.get('role')=='assistant','Unexpected OpenAI output item/tool')
            for part in item.get('content',[]):
                P.require(part.get('type')=='output_text','Refusal/nontext OpenAI output');pieces.append(part['text'])
        P.require(len(pieces)==1,'Expected one complete OpenAI text output');return pieces[0]
    P.require(provider=='anthropic' and obj.get('type')=='message' and obj.get('stop_reason')=='end_turn','Claude nonterminal/refusal/token cap')
    pieces=[]
    for part in obj.get('content',[]):
        P.require(part.get('type')=='text','Unexpected Claude tool/thinking/nontext block');pieces.append(part['text'])
    P.require(len(pieces)==1,'Expected one complete Claude text output');return pieces[0]
