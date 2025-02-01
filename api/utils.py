from pymongo import MongoClient, ReturnDocument
from django.conf import settings  # Import settings from Django

def get_next_sequence_value(collection_name):
    # Use the MongoDB connection string from settings.py
    client = MongoClient(settings.MONGOENGINE_CONNECTION_STRING)
    db = client[settings.MONGOENGINE_DATABASE_NAME]
    
    # Collection where sequence counters are stored
    counter = db['counters']

    # Increment the sequence value for the given collection
    sequence_document = counter.find_one_and_update(
        {'_id': collection_name},
        {'$inc': {'sequence_value': 1}},
        return_document=ReturnDocument.AFTER,
        upsert=True
    )
    
    # Return the updated sequence value
    return sequence_document['sequence_value']

def generate_id(prefix, collection_name):
    next_value = get_next_sequence_value(collection_name)
    return f"{prefix}{next_value:06d}"
