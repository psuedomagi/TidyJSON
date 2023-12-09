import json
from enum import Enum
from json import JSONDecoder, load, loads
from pathlib import Path
from typing import Any, Callable, Dict, List, Union

from attrs import define, field


@unique
class TidyErrorType(Enum):
    """
    An enumeration of error types that can occur in the TidyJSON module.

    Attributes
    ----------
        INVALID_CHARACTER: Represents an error where an invalid character is
        encountered.
        MISSING_BRACKET: Represents an error where a bracket is missing.
        MISSING_QUOTE: Represents an error where a quote is missing.
        UNEXPECTED_TOKEN: Represents an error where an unexpected token is
        encountered.
    """

    INVALID_CHARACTER = "Invalid Character"
    MISSING_BRACKET = "Missing Bracket"
    MISSING_QUOTE = "Missing Quote"
    UNEXPECTED_TOKEN = "Unexpected Token"


default_cls_args: dict[str, bool] = {"slots": False, "kw_only": True, "order": True}


@define(**default_cls_args)
class ErrorManager(Exception):
    """
    A custom exception class for handling errors in JSON parsing.

    This class extends the base Exception class and is used to manage errors
    specific to JSON parsing in TidyJSON. It provides detailed error
    information including the type of error, its position in the
    JSON string, and a context snippet of the JSON string where the error
    occurred.

    Attributes
    ----------
        error_type: A string representing the type of error encountered during
        parsing.
        position: An integer indicating the position in the JSON string where
        the error occurred.
        json_str: The JSON string being parsed when the error was encountered.
        error_context: A string representing a snippet of the JSON string
        around the error position, providing context to the error. This
        attribute is set during the initialization of the object.

    Methods
    -------
    No public methods

    Notes
    -----
    *Private Methods*:
        __attrs_post_init__: Initializes the error context and formats the error message.
        _get_context: Returns a substring of the JSON string surrounding the error position for context.
    """

    error_type: str = field()
    position: int = field()
    json_str: str = field()
    error_context: str = field(init=False)

    def __attrs_post_init__(self) -> None:
        """
        Initializes the error message with detailed information about the
        error.

        This method is called automatically after the object is initialized.
        It sets up the error context and formats the error message to include
        the type of error, its position in the JSON string, and the
        surrounding context where the error occurred.
        """
        error_context: str = self._get_context()
        message: str = f"{self.error_type} \n at position: {self.position} \n context: {error_context}"
        super().__init__(message)

    def _get_context(self) -> str:
        """
        Retrieves a substring of the JSON string surrounding the error
        position.

        This method provides a context snippet from the JSON string to help
        identify the location and
        nature of the parsing error. It extracts a substring centered around
        the error position, extending up to 10 characters before and after the
        position, or to the string's boundaries.

        Returns
        -------
        A substring of the JSON string providing context to the parsing
            error.
        """

        return self.json_str[
            max(0, self.position - 10) : min(len(self.json_str), self.position + 10)
        ]


@define(**default_cls_args)
class TidyJSONParser(JSONDecoder):
    """
    A custom JSON parser class for handling complex JSON parsing scenarios.

    This class extends the standard Python JSONDecoder class to provide
    enhanced parsing capabilities for handling nested and complex JSON
    structures. It also seeks to identify and fix malformed JSON, especially
    problem characters. It supports iterative and recursive
    parsing approaches, selecting which to use based on the structure of the
    json, and includes custom error handling.

    The class first uses the standard Python JSONDecoder and then applies its methods to the output.

    Attributes
    ----------
    json_str: A string representing the JSON data to be parsed.

    index: An integer representing the current position in the JSON string
        during parsing.

    json_out: Stores the output after parsing the JSON string. This
        attribute is set after initialization.

    Methods
    -------
    decode: Decodes a JSON string using the inherited method from JSONDecoder.

    postprocess: Performs post-processing on the parsed JSON data, a pipeline
        method that routes the initially decoded JSON through the class'
        processing methods.

    parse_json: Main method for parsing the JSON string, delegating parsing
        based on the current character.

    parse_object: Parses a JSON object and returns a dictionary.

    parse_array: Parses a JSON array and returns a list.

    parse_collection: A generalized method for parsing JSON collections like
        objects and arrays.

    skip_spaces_and_char: Skips spaces and a specified character in the JSON
        string during parsing.

    parse_string: Parses a JSON string value.

    parse_number: Parses a JSON number and returns an int or float.

    parse_boolean_or_null: Parses JSON literals 'true', 'false', and 'null'.

    get_char: Returns the current character in the JSON string at the parsing index, or None if the end is reached.

    Notes
    -----
    Inherits from the Python JSONDecoder class.

    *Private Methods*:
        __attrs_pre_init__: A pre-initialization method called before
            initializing the JSONDecoder.
        __attrs_post_init__: A post-initialization method called after
            initializing the JSONDecoder. It sets the `json_out` attribute with the parsed JSON data.
    """

    json_str: str = field()
    index: int = field()
    json_out: Any = field(init=False)

    def __attrs_pre_init__(self, *args, **kwargs) -> None:
        """
        A pre-initialization method called before initializing the JSONDecoder.

        This method is a part of the attrs library's lifecycle hooks and is
        called before the JSONDecoder initialization. It can be used to set up
        or modify initial conditions or arguments.

        Parameters
        ----------
        *args
            Variable length argument list for passage to JSONDecoder
        **kwargs
            Arbitrary keyword arguments for passage to JSONDecoder

        See Also
        --------
        __attrs_post_init__ : The corresponding post-initialization method.
        """
        super(TidyJSONParser, self).__init__(*args, **kwargs)

    def __attrs_post_init__(self, **kwargs) -> None:
        """
        A post-initialization method called after initializing the JSONDecoder.

        This method is invoked after the object is fully initialized. It
        processes the provided JSON string using the inherited `decode` method
        and stores the result in the `json_out` attribute.

        Parameters
        ----------
        **kwargs
            Arbitrary keyword arguments passed to the decode method.

        See Also
        --------
        __attrs_pre_init__ : The corresponding pre-initialization method.
        decode : Method used to decode the JSON string.
        """
        pyjson_processed: Any = super().decode(s=self.json_str, **kwargs)
        self.json_out = self.postprocess(parsed_json=pyjson_processed)

    def decode(self, s: str) -> Any:
        """
        Decodes a JSON string using the inherited method from JSONDecoder.

        Overrides the `decode` method of JSONDecoder to handle the custom parsing logic implemented in this class.

        Parameters
        ----------
        s : The JSON string to be decoded.

        Returns
        -------
        The decoded Python object from the JSON string.
        """

        return super(TidyJSONParser, self).decode(s=s)

    def postprocess(self, parsed_json: Any) -> Any:
        """
        Performs post-processing on the parsed JSON data.

        This method allows for additional processing or manipulation of the
        JSON data after it has been parsed.

        Parameters
        ----------
        parsed_json : The initially parsed JSON data, before any
        post-processing.

        Returns
        -------
        The post-processed JSON data.
        """

        return self.parse_json(parsed_json)

    def parse_json(self) -> Any:
        """
        Delegate parsing based on the current character in the JSON string.

        This method serves as a dispatcher to various parsing functions
        depending on the character at the current
        parsing position. It handles objects, arrays, strings, numbers, and
        boolean/null literals.

        Returns
        -------
        The parsed Python object corresponding to the current segment of the
        JSON string.

        Raises
        ------
        ErrorManager
            If an unexpected token is encountered during parsing.
        """

        parse_funcs: Any = [
            self.parse_object,
            self.parse_array,
            self.parse_string,
            self.parse_number,
            self.parse_boolean_or_null,
        ]
        strings: list[str] = ["{", "[", '"', "-", "t"]

        char: str | None = self.get_char()
        parse_map: Any = dict(zip(strings, parse_funcs))

        if char in parse_map:
            return parse_map[char]()
        elif char.isdigit():
            return self.parse_number()

        raise ErrorManager(
            error_type=TidyErrorType.UNEXPECTED_TOKEN,
            position=self.index,
            json_str=self.json_str,
        )

    def parse_object(self) -> Dict[str, Any]:
        """
        Parse an object in the JSON string and return a dictionary.

        This method is responsible for parsing JSON objects (delimited by
        curly braces {}) and converting them into Python dictionaries.

        Returns
        -------
        A dictionary representing the parsed JSON object.
        """

    def parse_array(self) -> List[Any]:
        """
        Parse an array in the JSON string and return a list.

        This method is responsible for parsing JSON arrays (delimited by
        square brackets []) and converting them into Python lists.

        Returns
        -------
        A list representing the parsed JSON array.
        """

        return self.parse_collection(
            end_char="]", parse_func=self.parse_json, delimiter=","
        )

    def parse_collection(
        self, end_char: str, parse_func: Callable, delimiter: str
    ) -> Dict[str, Any] | List[Any]:
        """
        Generalized method for parsing JSON collections (objects and arrays).

        This method provides a unified approach to parse both JSON objects and
        arrays. It handles the parsing logic, including delimiters and end
        characters, and delegates the parsing of individual elements to a
        specified function.

        Parameters
        ----------
        end_char : The character that signifies the end of the collection.

        parse_func : The function to call for parsing individual elements of
        the collection.

        delimiter : The character that separates elements in the collection.

        Returns
        -------
        The parsed collection, either a dictionary (for objects) or a list
        (for arrays).
        """

        self.index += 1  # Skip start character ('{' or '[')
        collection: Any = {} if end_char == "}" else []
        while self.get_char() != end_char and self.get_char() is not None:
            key_or_value: Any = parse_func()
            if isinstance(collection, dict):
                self.skip_spaces_and_char(char=delimiter)
                collection[key_or_value] = self.parse_json()
            else:
                collection.append(key_or_value)
            self.skip_spaces_and_char(char=",")
        self.index += 1  # Skip end character ('}' or ']')
        return collection

    def skip_spaces_and_char(self, char: str) -> None:
        """
        Skips over spaces and a specified character in the JSON string during
        parsing.

        This method advances the parsing index past any spaces and the
        specified character. It's typically used to skip over delimiters and
        whitespace in the JSON string.

        Parameters
        ----------
        char : The character to skip along with any spaces.
        """
        while self.get_char() in [char, " "]:
            self.index += 1

    def parse_string(self) -> str:
        """
        Parses a JSON string value.

        This method extracts a string value from the JSON string, handling the
        escape characters and quotes that define the boundaries of a JSON
        string.

        Returns
        -------
        The extracted string value from the JSON data.
        """

        start, self.index = self.index + 1, self.index + 1
        while self.get_char() != '"' and self.get_char() is not None:
            self.index += 1
        end: Any = self.index
        self.index += 1
        return self.json_str[start:end]

    def parse_number(self) -> Union[float, int]:
        """
        Parses a JSON number and returns it as an int or float.

        This method parses numeric values in the JSON string, distinguishing
        between integers and floating-point numbers based on the presence of a
        decimal point.

        Returns
        -------
        The parsed number, returned as a float if it contains a decimal point,
        otherwise as an int.
        """
        start: int = self.index
        while self.get_char() not in [None, ",", " ", "}", "]"]:
            self.index += 1
        num_str: str = self.json_str[start : self.index]
        return float(num_str) if "." in num_str else int(num_str)

    def parse_boolean_or_null(self) -> Union[bool, None]:
        """
        Parses JSON literals 'true', 'false', and 'null'.

        This method recognizes and converts the JSON literals 'true', 'false',
        and 'null' into their corresponding Python
        values: True, False, and None.

        Returns
        -------
        The boolean value True or False, or None, corresponding to the parsed JSON literal.

        Raises
        ------
        ErrorManager
            If the literal is not recognized as 'true', 'false', or 'null'.
        """
        for literal, value in (("true", True), ("false", False), ("null", None)):
            if self.json_str.startswith(literal, self.index):
                self.index += len(literal)
                return value
        raise ErrorManager(
            error_type=TidyErrorType.UNEXPECTED_TOKEN,
            position=self.index,
            json_str=self.json_str,
        )

    def get_char(self) -> Union[str, None]:
        """
        Returns the current character in the JSON string at the parsing index.

        This method provides the character at the current index of the JSON
        string. If the index is beyond the end of the string, it returns None.

        Returns
        -------
        The character at the current parsing index, or None if the end of the
        string is reached.
        """

        return self.json_str[self.index] if self.index < len(self.json_str) else None


@define(**default_cls_args)
class TidyJSON:
    """
    Primary API entrypoint for TidyJSON. You can access all functionality from
    this class, which acts as a master/controller class. TidyJSON supports
    string input either was a string/stream or from a file, and will
    automatically detect and shift approaches based on whether you provide a
    path-like string or a string directly. You may also provide a save
    location to save to a file when you are done.

    Most of the heavy lifting is done by the TidyJSONParser class, which is a
    subclass of Python's JSONDecoder class. This class handles the parsing of
    the JSON string and provides the parsed JSON data to the TidyJSON class.

    To decode and parse JSON, which is TidyJSON's primary function:

    Examples
    --------
    Encoding a string:
    ```python
    tidy = TidyJSON(json_input=my_json_string)
    decoded_string = tidy.decode
    ```

    Encoding a file, and saving to a file (note, strings will be automatically
    converted to Path objects):
    ```python
    my_json_file = "/path/to/my/json/file.json"

    my_new_encoded_save_location = "/path/to/my/new/save/location.json"

    tidy = TidyJSON(json_input=my_json_file,
    save_path=my_new_encoded_save_location)

    decoded_json_file = tidy.decode

    my_newly_encoded_file = tidy.encode
    ```

    Similarly, if you want to decode a file, and pipe the decoded stream to
    something else, you would just not pass a save_path (see below).

    You can always access the decoded and parsed JSON with the `json`
    attribute:

    ```python
    def foo(decoded_json):
        #do something with the decoded json
        pass

    def bar(encoded_json):
        #do something with the encoded json
        pass

    decoder = tidy.decode
    my_decoded_json = tidy.json
    encoder = tidy.encode

    #we could also use decoder here; .decode returns the json attribute
    foo_output = foo(my_decoded_json)
    bar_output = bar(encoder)
    ```

    Attributes
    ----------
    json_input: A string representing the path to the JSON file or the
        JSON data itself. This attribute is set only if JSON data is
        provided during initialization. If it isn't... well, you're not
        going to be able to do anything useful.

    json: Stores the parsed JSON data. This attribute is set after
        decoding the JSON input, and will be None until you use .decode.

    save_path: A string representing the path where the JSON data will be
        saved. This attribute is set only if a save path is provided.

    Methods
    -------

    decode: A property that decodes the JSON input into Python data
        structures and populates the `json` attribute.

    encode: A property that encodes the Python data structures back into a JSON formatted string or saves it to a file if `save_path` is provided.


    Notes
    -----
    The class uses properties for encoding and decoding to provide a simple
    and intuitive interface.

    The `_load_file`, `_load_string`, and `_check_for_file` methods are
    private utility methods:

    *Private Methods*:
        _load_file: Loads JSON data from a file specified in `json_input`.
        _load_string: Loads JSON data from a string in `json_input`.
        _check_for_file: Checks if `json_input` is a valid file path.
    """

    json_input: str = field(default=None, init=False)
    json: Any = field(default=None, init=False)
    save_path: str = field(default=None, init=False)

    def __attrs_post_init__(self) -> None:
        """
        A post-initialization method to check if `json_input` is a file path.

        This method is called automatically after the object is initialized.
        It checks if the provided `json_input` is a path to a JSON file. If
        so, it sets `json_input` as a Path object.
        """

        if self._check_for_file():
            self.json_input: Path = Path(self.json_input)

    @property
    def decode(self) -> Any:
        """
        Decodes the JSON input into Python data structures.

        This property method handles the decoding of JSON data. If
        `json_input` is a file path, it loads
        the JSON from the file. If it's a JSON string, it decodes the string
        directly.

        Returns
        -------
        The Python representation of the decoded JSON data.

        Raises
        ------
        ValueError
            If no JSON input is provided or if the input is not a valid JSON string or file path.
        """

        if not self.json_input:
            raise ValueError("No JSON input provided.")
        elif self._check_for_file():
            self.json: Any = self._load_file()
        else:
            self.json: Any = self._load_string()
        return self.json

    @property
    def encode(self) -> Union[None, str]:
        """
        Encodes Python data structures back into a JSON formatted string or
        saves it to a file.

        This property method handles the encoding of Python data structures to
        JSON. If a `save_path` is provided, it saves the JSON data to the
        specified file. Otherwise, it returns the JSON data as a string.

        Returns
        -------
        The JSON formatted string if no `save_path` is provided, otherwise None.

        Raises
        ------
        ValueError
            If there is no JSON data to encode.
        """

        if self.save_path:
            with open(file=self.save_path, mode="w") as f:
                json.dump(obj=self.json, fp=f, indent=4, strict=False)
        elif self.json:
            return json.dumps(strict=False)
        else:
            raise ValueError(
                "TidyJSON object has no data to encode in the instance json  attribute. Please pass data next time."
            )

    def _load_file(self) -> Any:
        """
        Loads JSON data from a file specified in `json_input`.

        This internal method reads a JSON file specified by the `json_input` path and parses it using the
        custom `TidyJSONParser`.

        Returns
        -------
        The Python representation of the loaded JSON data.
        """

        with open(file=Path(self.json_input), mode="r") as f:
            return load(fp=f, cls=TidyJSONParser(strict=False))

    def _load_string(self) -> None:
        """
        Loads JSON data from a string in `json_input`.

        This internal method parses a JSON string provided in `json_input`
        using the custom `TidyJSONParser`.

        Returns
        -------
        The method does not return a value but updates the `json` attribute of
        the instance.
        """
        return loads(s=self.json_input, cls=TidyJSONParser(strict=False))

    def _check_for_file(self) -> bool:
        """
        Checks if `json_input` is a valid file path.

        This internal method verifies whether the provided `json_input` is a
        path to an existing file.

        Returns
        -------
        True if `json_input` is a valid file path, False otherwise.
        """
        return Path(self.json_input).is_file()
