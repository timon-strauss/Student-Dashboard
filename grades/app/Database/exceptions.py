class NotFoundError(Exception):

    def __init__(self, entity: str, entity_id: int | str):
        super().__init__(f"{entity} with id {entity_id} not found")
        self.entity = entity
        self.entity_id = entity_id


class DatabaseNotStartedError(Exception):

    def __init__(self):
        super().__init__("Database not started, call db_start() first")
