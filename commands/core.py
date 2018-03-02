

class Command:

    """

    A command is any deliberate trigger of brobot


    Attributes
    ----------

    name : str
        the name of the command

    task : function
        the function that runs when the command is called

    help : str
        the long help for the command

    brief: str
        the short help for the command

    aliases : list
        the list of names that can invoke the command
        if none this defaults to the name of the command

    """

    def __init__(self, name, task, prefix="!",
                 help=None, brief=None, aliases=None):

        self.name = name
        self.task = task
        self.prefix = prefix
        self.help = help or "No help text currently"
        self.brief = brief or self.help
        self.aliases = aliases or name
        self.triggers = [prefix + alias for alias in self.aliases]

    def match(self, message):
        """
            determines whether a given message matches for this
            command or not. By default this means the first word in
            the message is the commands prefix + an alias
        """
        txt = message.content
        first_word = txt.split()[0]
        if first_word in self.triggers:
            return True
        else:
            return False
