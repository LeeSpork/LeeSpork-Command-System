"""
LeeSpork
2020-6-02 to 2021-2-23
A generic command system desgined to be extendable with arbitrary input methods in mind.
"""

class CommandMessage:
    """Objects to represent user input for an arbitrary command system.
    
    Contains information on what the command's arguments
    are, what user send it, and how to reply to them.
    
    It can be useful to make a subclass of this, e.g. in order to change the
    `reply` method to do something more advanced than just a print statement,
    or the `__init__` function to use something other than whitespace characters
    to split command arguments.
    """
    # Do-ers
    
    def __init__(self, text, user=None):
        self.text = text
        self.user = user
        # Split text into command name and arguments list:
        self.cmd_name, *self.args_list = self.text.split()
    
    def reply(self, message:str):
        """Sends message to the user as a responce to this command.
        
        This is the main thing you'd want to override if you're subclassing
        this for use with something other than the Python console.
        """
        print(message)
        
    # Getters
    
    def get_text(self) -> str:
        """Returns the original text sent by the user"""
        return self.text
    
    def get_user(self):
        """Returns the object that represents who entered the command."""
        return self.user
    
    def get_cmd_name(self) -> str:
        """Returns the name of the command entered (with no arguments after it)"""
        return self.cmd_name
    
    def get_args_list(self) -> list:
        """Returns the list of command arguments entered by the user."""
        return self.args_list
    
    def get_args_str(self) -> str:
        """Returns the args as the entire string after the command name and first space."""
        return self.text[ len(self.cmd_name) +1 : ]
        # + 1 to remove the space that obviously must seperate the command and the args
        # Also pro tip: this won't throw an error e.g. in a case such as "1234"[5:] -> ""
        # -- 2020-9-27




class CommandSystem:
    
    # Exceptions
    
    class UnknownCommandError(Exception): pass
    class CommandAlreadyExistsError(Exception): pass
    
    # Objects
    
    class CommandHandler:
        """Objects of commands & their functions.
        
        Attributes that it should have:
          parent_system : Reference to the CommandSystem object that this command is a part of.
          name : The single word that is used to invoke this command.
          function : The actual Python function object that this command does.
          syntax : String that describes how to use (write) this command.
          description : String that describes what the command does
          aliases : List of strings that can be used instead of `name`
        
        """
         # No __init__ needed;
         # It should only ever be constructed by CommandSystem.add_cmd,
         # which will initilize these objects for us.
        
        def add_alias(cmd_obj, alias:str):
            """Makes it so you can use the alias in place of the command's name in the command system."""
            # Register it in the command system
            cmd_obj.parent_system._add_alias(cmd_obj, alias)
            # Remember it in case a help command wants to know
            cmd_obj.aliases.append(alias)
            # Return self so that this function can be chained or whatever
            return cmd_obj
        
        def add_aliases(cmd_obj, *aliases:str):
            """Adds multiple aliases for this command at once."""
            # Register them in the command system
            for alias in aliases:
                cmd_obj.parent_system._add_alias(cmd_obj, alias)
            # Remember our new aliases in case a help command wants to know them
            cmd_obj.aliases.extend(aliases)
            # Return self so that this function can be chained or whatever idk
            return cmd_obj
        
        def __str__(self):
            return self.name
        
        def __call__(self, cmd_message_oject, **kwargs):
            """See the 'function' attribute of this object."""
            return self.function(cmd_message_oject, **kwargs)
    
    
    # Instance methods of CommandSystem
    
    def __init__(self):
        # Set of all command names, not including aliases
        self._cmds = set()
        
        # Dict of all command names, including aliases
        self._cmd_names = {}


    def add_command(sys, syntax:str, function, description="(No description)") -> CommandHandler:
        """Registers a new command into the system.
        The first word of syntax will become the command name.
        
        e.g.
        syntax = "command_name <required argument> [optional argument]",
        function = lambda cmd: cmd.reply("Hello " + cmd.get_args()[0])
        """
        # The "command name" is the first word of the syntax
        command_name = syntax.split(maxsplit=1)[0]
        
        # Initilize command object
        obj = sys.CommandHandler()
        obj.parent_system = sys
        obj.name = command_name
        obj.function = function
        obj.syntax = syntax
        obj.description = description
        obj.aliases = []
        # Register the name as an alias in order to add it to the dictionary of all command names
        obj.add_alias(command_name)
        
        # Add the it to the set of all commands
        sys._cmds.add(command_name)
        
        # Return the object, which is useful for adding aliases.
        return obj
    
    add_cmd = add_command
    
    
    def run_command(command_system, command_message_handler_object:CommandMessage):
        """Tries to run the command."""
        # Get the name of the command from the message:
        command_name = command_message_handler_object.get_cmd_name()
        
        try:
            # Get the Python function for the command from the name of the command:
            command_function = command_system.get_command(command_name).function
        
        except KeyError:
            # Or if there is no command with that name:
            #raise command_system.UnknownCommandError("Unknown command {}".format(repr(command_name)))
            command_message_handler_object.reply(
                f"Error: Unknown command {repr(command_name)}"
            )
        
        else:
            # Run the function for the command, which takes the single argument of the command message:
            return command_function(command_message_handler_object)
    
    
    def get_all_command_names(self) -> set:
        """Returns a set containing the name of every command (not including aliases)."""
        return self._cmds.copy()
    
    
    def get_command(command_system, command_name_or_alias) -> CommandHandler:
        """Returns the object representing a command."""
        return command_system._cmd_names[command_name_or_alias]
    
    
    def _add_alias(self, cmd_obj:CommandHandler, new_alias:str):
        """Makes new_alias an alias of the given command
        such that you can use it instead of its name in this command system.
        
        Pro tip: use CommandHandler.add_alias as a shortcut to this.
        """
        # Error check: does the command name already exist?
        if new_alias in self._cmd_names:
            raise CommandAlreadyExistsError(
                "The command name {} is already used by the {} command in this system."
                .format( repr(new_alias), self._cmd_names[new_alias] )
            )
        
        # Add to the dictionary of command names
        else: self._cmd_names[new_alias] = cmd_obj



if __name__ == "__main__":
    
    # Example system
    
    # some variables
    user_quit = False
    
    # Create a new command system
    my_cmd_sys = CommandSystem()
    
    # Create commands by first defining their functions
    
    def cmd_list_commands(msg):
        """Replies to the message with a list of commands."""
        all_cmds = my_cmd_sys.get_all_command_names() # Set of the names of all commands
        output = ", ".join(all_cmds)
        msg.reply(output)
    
    
    def cmd_cmd_help(msg):
        """Replies to the message with help on a specific command."""
        command = my_cmd_sys.get_command(msg.get_args_str())
        msg.reply(f"""Help for {command.name}:
Syntax: {command.syntax}
Description: {command.description}
Aliases: {", ".join(command.aliases)}"""
        )
        
        
    def cmd_help(msg):
        num_args = len(msg.get_args_list())
        if num_args == 0:
            return cmd_list_commands(msg)
        
        elif num_args == 1:
            return cmd_cmd_help(msg)
        else:
            msg.reply(f"Error: you supplies {num_args} arguments, but help only uses zero or one.")
    
    my_cmd_sys.add_command("help [command]", cmd_help, "Lists all avaliable commands or gets information for a specific command.").add_aliases("?")
    
    
    def cmd_quit(msg):
        global user_quit
        user_quit = True
    
    my_cmd_sys.add_command("quit", cmd_quit, "Quits this example command system's input loop.") \
        .add_aliases("leave", "end", "stop")
    
    # Now for some UI
    print("Welcome to the example command system!")
    print('Type "help" for a list of commands, and "help <command>" for help on a specific command.')
    
    # An infinite loop so that the user can keep entering commands
    while not user_quit:
        input_string = input("> ")
        input_object = CommandMessage(input_string)
        my_cmd_sys.run_command(input_object)