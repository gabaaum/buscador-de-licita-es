import json

def fix_payload():
    with open('pbi_table_request.json', 'r') as f:
        payload = json.load(f)
    
    # Try to find Top N limitation and increase it
    try:
        commands = payload.get('queries', [{}])[0].get('Query', {}).get('Commands', [])
        for cmd in commands:
            if 'SemanticQueryDataShapeCommand' in cmd:
                binding = cmd['SemanticQueryDataShapeCommand'].get('Binding', {})
                if 'DataReduction' in binding:
                    if 'DataVolume' in binding['DataReduction']:
                        binding['DataReduction']['DataVolume'] = 4 # 4 means maximum usually
                    if 'Primary' in binding['DataReduction']:
                        if 'Window' in binding['DataReduction']['Primary']:
                            binding['DataReduction']['Primary']['Window']['Count'] = 500
                else:
                    # Inject DataReduction manually if missing
                    cmd['SemanticQueryDataShapeCommand']['Binding']['DataReduction'] = {
                        "DataVolume": 4,
                        "Primary": {
                            "Window": {
                                "Count": 500
                            }
                        }
                    }
                    
        with open('pbi_table_request_500.json', 'w') as f:
            json.dump(payload, f)
        print("Payload ajustado para 500 itens salvo em pbi_table_request_500.json")
    except Exception as e:
        print("Erro ao ajustar:", e)

fix_payload()
