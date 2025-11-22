# Reserved for future message-testing utilities.
# Not used in production since Lambda is triggered by SQS → configured in EB.

def test_event():
    return {
        "Records": [{
            "body": '{"product": "test", "quantity": 2, "customer": "demo"}'
        }]
    }
