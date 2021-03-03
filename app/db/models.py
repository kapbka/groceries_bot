from mongoengine import Document, EmbeddedDocument, EmbeddedDocumentField, EmbeddedDocumentListField,\
    StringField, BooleanField, IntField, DictField, BinaryField


class Cred(EmbeddedDocument):
    login = StringField(required=True)
    password = BinaryField()
    cvv = IntField()


class AutoBook(EmbeddedDocument):
    enabled = BooleanField(default=False)
    interval = IntField()
    filters = DictField(default={})


class Chain(Document):
    chat_id = IntField(required=True)
    name = StringField(required=True)
    creds = EmbeddedDocumentField(Cred, default=Cred)
    autobook = EmbeddedDocumentField(AutoBook, default=AutoBook)
