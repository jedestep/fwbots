from mongodb import MongoDBPersister

def get_backend(name):
    backends = {
        'mongodb': MongoDBPersister,
    }
    return backends[name]
