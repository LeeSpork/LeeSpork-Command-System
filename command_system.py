"""
Author: LeeSpork
Version: 1.215.05
Created 2020-6-02 to 2020-6-21 as LeeSpork_Command_System_206
Updated 2021-5-05 as command_system_215
A general command system, desgined to be able to handle arbitrary input methods.
"""

# User I/O handler class

class CommandMessage:
    """Specifies objects that handle I/O with a CommandSystem.
    
    Initalised with the command text,
    and any additional information that may be needed to run the command.
    
    Has functionality that command should use such as:
    * getting the arguments of the command
    * relaying a message back to the user
    
    Can be overrided to change the functionality of the reply method
    to adapt it to any output device.
    """
    # Do-ers
    
    def __init__(self, text:str, **params):
        """
        text: a string such as "attack dragon"
        params: any additional information that a command might need,
                such as user=user.id, location=user.location, game=game_object
        """
        self.text = text
        self.params = params
        # Split text into command name and arguments list:
        self.cmd_name, *self.args_list = self.text.split()
        
        self.last_command_system = None
    
    def reply(self, message:str):
        """Displays a message to the user.
        
        This is the main thing you'd want to override if you're subclassing this
        class for use with something other than the Python console.
        """
        print(message)
        
    # Getters
    
    def get_text(self) -> str:
        """Returns the original text sent by the user"""
        return self.text
    
    def get_cmd_name(self) -> str:
        """Returns the name of the command entered (with no arguments after it)"""
        return self.cmd_name
    
    def get_args_list(self) -> list:
        """Returns the list of command arguments entered by the user."""
        return self.args_list
    
    def get_args_str(self) -> str:
        """Returns the args as the entire string of the command text, minus the command name (+ a space)."""
        return self.text[ len(self.cmd_name) +1 : ]
        # + 1 to remove the space that obviously must seperate the command and the args
        # Also pro tip: this won't throw an error e.g. in a case such as "1234"[5:] -> ""
        # -- 2020-9-27
    
    def get_param(self, param, default=None):
        """Return the value for param if it was passed as a keyword argument when this object was created, else default."""
        return self.params.get(param, default=default)
    
    def get_last_command_system(self):
        """When running a command in a CommandSystem using this CommandMessage object, the CommandSystem will update this to be itself before running the command."""
        return self.last_command_system
    
    def set_last_command_system(self, new_current_system):
        """CommandSystem objects will use this. Might be useful for implementing, for exmaple, a help command."""
        self.last_command_system = new_current_system




# class of the actual command system

class CommandSystem:
    """LeeSpork's Command System.
    
    How to use:
    1. Create an instance of it
    2. add commands using either the add_command method or the define_command decorator.
       Command use python functions and are expected to have one parameter,
       which is expected to be an instance of CommandMessage or a subclass thereof.
    3. run commands by creating a CommandMessage (or subclass thereof) object,
       and pass it into the run_command method of your CommandSystem.
    
    There is an example at the bottom of this file.
    """
    
    # Exceptions
    
    class CommandError(Exception):
        """Exception that may be raised by a command."""
        pass
    
    class UnknownCommandError(CommandError):
        command_name = "<Unspecified command name>"
        def __init__(self, attempted_command_name, *args, **kwargs):
            self.command_name = attempted_command_name
            super().__init__(f"Unknown command {repr(self.command_name)}", *args, **kwargs)
    
    class CommandSyntaxError(CommandError): pass
    
    class CommandAlreadyExistsError(Exception): pass
    
    # Objects
    
    class CommandHandler:
        """Objects of commands & their functions.
        
        Attributes that it should have:
          parent_system : Reference to the CommandSystem object that this command is a part of.
          name : The single word that is typed to invoke this command.
          function : The actual Python function object that this command does.
          syntax : String that describes how to use (write) this command.
          description : String that describes what the command does
          aliases: List of aliases
        
        """
         # No __init__ needed;
         # It should only ever be constructed by CommandSystem.add_cmd,
         # which will initilize these objects for us.
        
        def add_alias(cmd_obj, alias:str):
            """Makes it so you can use the alias in place of the command's name in the command system."""
            cmd_obj.parent_system._add_alias(cmd_obj, alias)
            cmd_obj.aliases.append(alias)
            return cmd_obj # Return this object itself so that you can chain this function or whatever
        
        def __str__(self):
            return self.name
        
        def __call__(self, cmd_message_oject, **kwargs):
            """See the 'function' attribute of this object."""
            return self.function(cmd_message_oject, **kwargs)
    
    
    # Instance methods of CommandSystem
    
    def __init__(self):
        # Set of all command names, not including aliases
        self._cmd_names = set()
        
        # Dict of all command names and aliases -> 
        self._cmd_objs = {}
    
    
    def define_command(sys, *args, **kwargs):
        """Can be used as a decorator of a function to add a command into the command system.
        
        Parameters are expected to match add_command, sans function.
        
        Returns a callable wrapper of add_command with one parameter: the function parameter for add_command.
        """
        def decorator(function):
            return sys.add_command(function, *args, **kwargs)
        
        return decorator


    def add_command(sys, function, syntax:str, aliases=[], desc="(No description)") -> CommandHandler:
        """Registers a new command into the system.
        
        function: 
          A function.
          Should have one parameter, which is expect to be an object,
          (usually of CommandMessage or a subclass thereof)
          which has the following methods:
            * reply(string) - displays text to the user that issued the command
            * get_text() - gets the command text issued by the user, e.g. "foo bar pop"
            * get_cmd_name() - gets the name of the command issued by the user, e.g. the first word, e.g. "foo"
            * get_cmd_args_list() - gets a list of the arguments after the cmd_name, e.g. ["bar", "pop"]
            * get_cmd_args_str() - gets the arguments after the cmd_name as one string, e.g. "bar pop"
            * get_param(param) - returns the object set as the user
            * get_last_command_system() - returns the command system that the object was last ran in
            * set_last_command_system(sys) - is used by the run_command method of command systems
        
        syntax:
          a string, e.g. "command_name <required argument> [optional argument]"
          The first word is automatically becomes the name of the command.
        
        aliases:
          a collection of strings that can be used instead of the command_name provided by syntax.
          They should not already be assigned to commands in the system.

        desc:
          an optional string that describes what a command does.
          Mainly here just in case you want there to be a help command.
        """
        # The "command name" is the first word of the syntax
        command_name = syntax.split(maxsplit=1)[0]
        
        # Initilize command object
        obj = sys.CommandHandler()
        obj.parent_system = sys
        obj.name = command_name
        obj.function = function
        obj.syntax = syntax
        obj.aliases = []
        obj.desc = desc
        obj.description = desc # More descriptive but more annoying to spell alias
        
        # Register the command name as an alias, which will add it to the command system
        obj.add_alias(command_name)
        
        # Add all aliases
        for alias in aliases:
            obj.add_alias(alias)
        
        # Something else that may be useful idk
        obj.__call__ = obj.function
        
        # Add the it to the set of all commands
        sys._cmd_names.add(command_name)
        
        return obj
    
    
    def run_command(command_system, command_message_handler_object):
        """Takes a CommandMessage object (or object of a subclass of CommandMessage) and executes its command.
        
        Returns the return value of the command function.
        """
        # Firstly, tell the CommandMessage object that we are using it.
        command_message_handler_object.set_last_command_system(command_system)
        
        # Get the name of the command from the message:
        command_name = command_message_handler_object.get_cmd_name()
        
        try:
            # Get the Python function for the command from the name of the command:
            command_function = command_system._cmd_objs[command_name].function
        
        except KeyError:
            # Or if there is no command with that name:
            error = command_system.UnknownCommandError(command_name)
            
            raise error
        
        else:
            # Run the function for the command, which takes the single argument of the command message:
            return command_function(command_message_handler_object)
    
    
    def _add_alias(self, cmd_obj:CommandHandler, new_alias:str):
        """Makes new_alias an alias of the given command
        such that you can use it instead of its name in this command system.
        
        Pro tip: use CommandHandler.add_alias as a shortcut to this.
        """
        # Error check: does the command name already exist?
        if new_alias in self._cmd_objs:
            raise CommandAlreadyExistsError(
                "The command name {} is already used by the {} command in this system."
                .format( repr(new_alias), self._cmd_objs[new_alias] )
            )
        
        # Add to the dictionary of command names
        else: self._cmd_objs[new_alias] = cmd_obj




# Example command function
        
def example_help_command_function(msg):
    """The function for an example help command you could add to your command system.
    
    To add it to your system, you can use something like:
    
    CMD_SYS = CommandSystem()
    CMD_SYS.add_command(
        "help [command]", example_help_command_function,
        description="Provides a list of valid commands, or information on a specific command.",
        aliases=["?"]
    )
    """
    cmd_sys = msg.get_last_command_system() # Get the command system so we can find the commands
    all_cmd_names = cmd_sys._cmd_names # Set of the names of all commands
    args = msg.get_args_str()
    if args == "":
        # List off all the commands.
        msg.reply(
            "Commands:\n" +
            ", ".join(all_cmd_names) +
            "\nUse 'help [command]' for more information on a command."
            )
    else:
        # Is there a command with the name of the passed argument?
        command_name = args
        found_command = None
        try:
            found_command = cmd_sys._cmd_objs[command_name]
        except KeyError:
            raise cmd_sys.UnknownCommandError(command_name)
        if found_command is not None:
            found_syntax = found_command.syntax
            found_description = found_command.description
            found_aliases = ", ".join(found_command.aliases)
            msg.reply(f"Help for {repr(command_name)}:\nSyntax: {found_syntax}\nAliases: {found_aliases}\nDescription: {found_description}")




if __name__ == "__main__":
    
    # Example system
    
    CMD_SYS = CommandSystem()
    running = True
    
    # Add a command using a pre-existing function
    CMD_SYS.add_command(
        example_help_command_function,
        "help [command]", aliases=["?"],
        desc="Provides a list of valid commands, or information on a specific command."
    )
    
    # Add a command by defining a function with a decorator
    @CMD_SYS.define_command("exit", aliases=["quit", "end", "stop"], desc="Exits the input loop.")
    def cmd_exit(msg):
        msg.reply("Thank you for using the command system example. Have a nice day!")
        global running
        running = False
    
    @CMD_SYS.define_command(
        "add <number1> <number2>", aliases=["sum"],
        desc="Calculates the sum of two numbers"
    )
    def cmd_add(msg):
        args = msg.get_args_list()
        if len(args) != 2:
            raise msg.get_last_command_system().CommandSyntaxError("there must be two arguments")
        try:
            num1 = float(args[0])
            num2 = float(args[1])
        except ValueError as err:
            raise msg.get_last_command_system().CommandSyntaxError(str(err))
        the_sum = num1 + num2
        msg.reply(f"The sum of {args[0]} and {args[1]} is about {the_sum}")
    
    @CMD_SYS.define_command("ping")
    def cmd_ping(msg):
        msg.reply("Hello")
    
    print("Welcome to the example command system!\nEnter 'help' for a list of commands.")
    # Input loop
    while running:
        # Get user input
        command_text = input("\n> ")
        command_input_object = CommandMessage(command_text)
        try:
            # Run the command
            CMD_SYS.run_command(command_input_object)
        except CMD_SYS.UnknownCommandError as err:
            # Handle error raised if the user inputed an invalid command name
            print(f"Unknown command {repr(err.command_name)}")
        except CMD_SYS.CommandError as err:
            print(f"Error: {err}")
