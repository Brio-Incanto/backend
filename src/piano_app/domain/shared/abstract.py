def abstract[T: type](cls: T) -> T:
    """Forbid direct instantiation of ``cls`` while its subclasses stay constructible.

    A runtime stand-in for an abstract base where no ``@abstractmethod`` fits — a
    fully concrete yet semantically abstract base — and ABCMeta/slots friction is
    unwanted. Installs a ``__new__`` guard that raises when the exact decorated class
    is instantiated; any subclass constructs normally.
    """

    def guarded_new(instance_cls: type, *args: object, **kwargs: object) -> object:
        if instance_cls is cls:
            raise TypeError(f"{cls.__name__} is abstract and cannot be instantiated directly.")

        return object.__new__(instance_cls)

    cls.__new__ = guarded_new  # type: ignore[assignment]
    return cls
