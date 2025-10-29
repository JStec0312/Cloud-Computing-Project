from src.infrastructure.uow import SqlAlchemyUoW
from src.application.logbook_service import LogbookService
class FileService:
    def __init__(self, uow: SqlAlchemyUoW, logbook: LogbookService):
        self.uow = uow
        self.logbook = logbook