class AbstractCommand(object):
    """
      Change the docstring of the command class to set the description of the command.
    """
    #: CLI command alias
    alias = None

    def __init__(self, **kwargs):
        self.__dict__ = kwargs

    def __getattr__(self, attr):
        try:
            super(AbstractCommand, self).__getattr__(attr)
        except Exception:
            return None

    @classmethod
    def name(cls):
        """ Name of the command """
        return cls.__name__.lower()

    @classmethod
    def make_args(cls, *args, **kwargs):
        """ Helper method to compose arguments for :meth:`arguments` """
        return args, kwargs

    @classmethod
    def docs(cls):
        """
        Split the param description from from the class's __doc__

        :return: Tuple of (help_doc, param_docs) where help_doc is the part before :param, and param_docs is a dict of param -> param doc.
        :rtype: tuple(str, dict(str, str))
        """
        doc_parts = cls.__doc__ and cls.__doc__.split(':param ')

        # Try to get / merge from parent class
        if not doc_parts or super(cls, cls).__doc__ != cls.__doc__:
            doc_parts_old = super(cls, cls).__doc__.split(':param ')
            # Merge parent class docs (just the params part)
            if not doc_parts:
                doc_parts = doc_parts_old
            else:
                doc_parts.extend(doc_parts_old[1:])  # params
                if not doc_parts[0].strip():      # description
                    doc_parts[0] = doc_parts_old[0]

        doc = doc_parts[0].rstrip()
        params = {}

        for doc_part in doc_parts[1:]:
            type_param, param_doc = doc_part.split(':', 1)
            param = type_param.split()[-1]
            params[param] = param_doc.strip()

        return doc, params

    @classmethod
    def arguments(cls):
        """
          List of arguments to be passed to argparse's add_argument.
          Optionally, return a tuple of two lists where first one consists
          of normal arguments, and the 2nd one consists of chaining arguments.

          Use :meth:`make_args` to create the args::

            return [cls.make_args('--name', help='Product name')]

          Or return a tuple of two lists where the 2nd one consists of chaining options::

            return ([cls.make_args('--name', help='Product name')],
                    [cls.make_args('--test', help='Run tests after commit')])


          :return: List of add_argument params or tuple of two lists
        """
        return []

    def run(self):
        raise NotImplementedError('%s has not implemented run()' % self.__class__.__name__)
