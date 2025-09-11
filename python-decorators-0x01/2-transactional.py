def transactional(func):
    def wrapper(db, *args, **kwargs):
        try:
            db.begin()  # Start transaction
            result = func(db, *args, **kwargs)
            db.commit()  # Commit if no error
            return result
        except Exception as e:
            db.rollback()  # Rollback on error
            raise
    return wrapper