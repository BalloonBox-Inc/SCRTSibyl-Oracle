from os import path
import json


def read_config_file(loan_request):

    config_file = path.join(path.dirname(__file__), 'config.json')

    with open(config_file) as f:
        data = json.load(f)['data']
        data = [d for d in data
                if d['maximum_amount'] >= loan_request][0]

    return data


def read_models_and_metrics(d):
    keys = [*d]
    values = list(d.values())

    model_values = [d['weight'] for d in values]
    models = dict(zip(keys, model_values))

    metric_values = [d['metrics'] for d in values]
    metrics = {k: v for d in metric_values for k, v in d.items()}

    return models, metrics


def read_model_penalties(d):
    keys = [*d]
    values = list(d.values())

    model_values = [d['penalty_weight'] for d in values]
    models = dict(zip(keys, model_values))

    return models


def create_feedback(d):
    return {k: {} for k, v in d.items()}
