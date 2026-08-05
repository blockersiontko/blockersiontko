#!/usr/bin/env python3
"""
Brainfuck Interpreter in Python
Author: Max Base
Date: 03/12/2025
Repository: https://github.com/BaseMax/brainfuck-interpreter-python
License: MIT
"""

import sys
import os
import argparse
import logging
from typing import List, Tuple, Optional

# -----------------------------------------------------------------------------
# Module Metadata and Configuration
# -----------------------------------------------------------------------------
__version__ = f"{1}.{0}.{0}"
__author__ = "Max Base"

logging.basicConfig(level=logging.ERROR, format='%(levelname)s: %(message)s')

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
TAPE_SIZE = 30000

TOKEN_PLUS       = '+'
TOKEN_MINUS      = '-'
TOKEN_NEXT       = '>'
TOKEN_PREVIOUS   = '<'
TOKEN_OUTPUT     = '.'
TOKEN_INPUT      = ','
TOKEN_LOOP_START = '['
TOKEN_LOOP_END   = ']'
TOKEN_BREAK      = '#'

# -----------------------------------------------------------------------------
# Custom Exceptions
# -----------------------------------------------------------------------------
class BrainfuckRuntimeError(Exception):
    """Exception for runtime errors in the Brainfuck interpreter."""
    pass

class BrainfuckParseError(Exception):
    """Exception for errors during parsing of Brainfuck code."""
    pass

# -----------------------------------------------------------------------------
# Data Classes
# -----------------------------------------------------------------------------
class BrainfuckInstruction:
    """
    Represents a single Brainfuck instruction.
    
    Attributes:
        token (str): The Brainfuck token (e.g. '+', '-', etc.).
        difference (int): The net effect of consecutive same tokens.
        loop (Optional[List[BrainfuckInstruction]]): For loops, the list of instructions inside.
    """
    def __init__(self, token: str, difference: int = 1,
                 loop: Optional[List['BrainfuckInstruction']] = None) -> None:
        self.token = token
        self.difference = difference
        self.loop = loop

    def __repr__(self) -> str:
        if self.token == TOKEN_LOOP_START:
            return f"Instr({self.token}, diff={self.difference}, loop={self.loop})"
        return f"Instr({self.token}, diff={self.difference})"

class BrainfuckExecutionContext:
    """
    Holds the execution context for a Brainfuck program.
    
    Attributes:
        tape (List[int]): The memory tape.
        tape_index (int): The current index on the tape.
        tape_size (int): Total size of the tape.
        should_stop (bool): Flag to stop execution.
        output_handler (callable): Function to handle output.
        input_handler (callable): Function to handle input.
    """
    def __init__(self, tape_size: int) -> None:
        self.tape = [0] * tape_size
        self.tape_index = 0
        self.tape_size = tape_size
        self.should_stop = False
        self.output_handler = lambda x: sys.stdout.write(chr(x))
        self.input_handler = brainfuck_getchar

# -----------------------------------------------------------------------------
# I/O Utility
# -----------------------------------------------------------------------------
def brainfuck_getchar() -> str:
    """
    Reads exactly one character from stdin and discards the rest of the line.
    
    Returns:
        str: The character read.
    """
    ch = sys.stdin.read(1)
    while True:
        t = sys.stdin.read(1)
        if t == '\n' or t == '':
            break
    return ch

# -----------------------------------------------------------------------------
# Parsing Functions
# -----------------------------------------------------------------------------
def parse_brainfuck(code: str, index: int = 0, end: Optional[int] = None,
                    inside_loop: bool = False) -> Tuple[List[BrainfuckInstruction], int]:
    """
    Recursively parses Brainfuck code into a list of instructions.
    
    Consecutive tokens (e.g. '+' or '>') are merged by computing a "difference".
    If inside a loop (inside_loop=True), the function stops when a matching ']' is found.
    
    Args:
        code (str): The Brainfuck code.
        index (int): Starting index.
        end (Optional[int]): Ending index; if None, uses len(code).
        inside_loop (bool): True if parsing inside a loop.
    
    Returns:
        Tuple[List[BrainfuckInstruction], int]: Parsed instructions and new index.
    
    Raises:
        BrainfuckParseError: If an unmatched loop marker is detected.
    """
    if end is None:
        end = len(code)
    instructions: List[BrainfuckInstruction] = []
    while index < end:
        c = code[index]
        index += 1
        if c not in (TOKEN_PLUS, TOKEN_MINUS, TOKEN_NEXT, TOKEN_PREVIOUS,
                     TOKEN_OUTPUT, TOKEN_INPUT, TOKEN_LOOP_START, TOKEN_LOOP_END, TOKEN_BREAK):
            continue
        if c == TOKEN_LOOP_START:
            loop_instructions, index = parse_brainfuck(code, index, end, inside_loop=True)
            instructions.append(BrainfuckInstruction(TOKEN_LOOP_START, 1, loop_instructions))
        elif c == TOKEN_LOOP_END:
            if not inside_loop:
                raise BrainfuckParseError("Unexpected ']' encountered at position {}".format(index-1))
            return instructions, index
        elif c in (TOKEN_PLUS, TOKEN_MINUS):
            diff = 1
            while index < end and code[index] in (TOKEN_PLUS, TOKEN_MINUS):
                diff = diff + 1 if code[index] == c else diff - 1
                index += 1
            instructions.append(BrainfuckInstruction(c, diff))
        elif c in (TOKEN_NEXT, TOKEN_PREVIOUS):
            diff = 1
            while index < end and code[index] in (TOKEN_NEXT, TOKEN_PREVIOUS):
                diff = diff + 1 if code[index] == c else diff - 1
                index += 1
            instructions.append(BrainfuckInstruction(c, diff))
        elif c in (TOKEN_OUTPUT, TOKEN_INPUT):
            diff = 1
            while index < end and code[index] == c:
                diff += 1
                index += 1
            instructions.append(BrainfuckInstruction(c, diff))
        elif c == TOKEN_BREAK:
            instructions.append(BrainfuckInstruction(c, 1))
    if inside_loop:
        raise BrainfuckParseError("Unmatched '[' detected")
    return instructions, index

def parse_string(code: str) -> List[BrainfuckInstruction]:
    """
    Parses an entire Brainfuck code string into a list of instructions.
    
    Args:
        code (str): The Brainfuck code.
    
    Returns:
        List[BrainfuckInstruction]: The parsed instructions.
    
    Raises:
        BrainfuckParseError: If parsing fails.
    """
    instructions, _ = parse_brainfuck(code)
    return instructions

# -----------------------------------------------------------------------------
# Execution Functions
# -----------------------------------------------------------------------------
def execute_instruction(instr: BrainfuckInstruction, context: BrainfuckExecutionContext) -> None:
    """
    Executes a single Brainfuck instruction using the provided context.
    
    Args:
        instr (BrainfuckInstruction): The instruction to execute.
        context (BrainfuckExecutionContext): The execution context.
    
    Raises:
        BrainfuckRuntimeError: On tape pointer errors.
    """
    token = instr.token
    diff = instr.difference

    if token == TOKEN_PLUS:
        context.tape[context.tape_index] = (context.tape[context.tape_index] + diff) % 256

    elif token == TOKEN_MINUS:
        context.tape[context.tape_index] = (context.tape[context.tape_index] - diff) % 256

    elif token == TOKEN_NEXT:
        new_index = context.tape_index + diff
        if new_index >= context.tape_size:
            raise BrainfuckRuntimeError(f"Tape overrun: attempted index {new_index}, tape size is {context.tape_size}")
        context.tape_index = new_index

    elif token == TOKEN_PREVIOUS:
        new_index = context.tape_index - diff
        if new_index < 0:
            raise BrainfuckRuntimeError("Tape underrun: negative tape index")
        context.tape_index = new_index

    elif token == TOKEN_OUTPUT:
        for _ in range(diff):
            context.output_handler(context.tape[context.tape_index])
        sys.stdout.flush()

    elif token == TOKEN_INPUT:
        for _ in range(diff):
            ch = context.input_handler()
            context.tape[context.tape_index] = 0 if ch == '' else ord(ch)

    elif token == TOKEN_LOOP_START:
        while context.tape[context.tape_index] != 0:
            brainfuck_execute(instr.loop, context)

    elif token == TOKEN_BREAK:
        low = max(0, context.tape_index - 10)
        high = min(context.tape_size, low + 21)
        indices = "\t".join(str(i) for i in range(low, high))
        values = "\t".join(str(context.tape[i]) for i in range(low, high))
        pointer_line = "\t".join("^" if i == context.tape_index else " " for i in range(low, high))
        print(indices)
        print(values)
        print(pointer_line)
    else:
        pass

def brainfuck_execute(instructions: List[BrainfuckInstruction], context: BrainfuckExecutionContext) -> None:
    """
    Executes a list of Brainfuck instructions using the provided context.
    
    Args:
        instructions (List[BrainfuckInstruction]): The instructions to execute.
        context (BrainfuckExecutionContext): The execution context.
    """
    for instr in instructions:
        if context.should_stop:
            break
        execute_instruction(instr, context)

# -----------------------------------------------------------------------------
# Run Modes
# -----------------------------------------------------------------------------
def run_file(filename: str) -> bool:
    """
    Reads Brainfuck code from a file and executes it.
    
    Args:
        filename (str): Path to the Brainfuck file.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        with open(filename, 'r') as f:
            code = f.read()
    except Exception as e:
        logging.error(f"Failed to read file {filename}: {e}")
        return False

    try:
        instructions = parse_string(code)
    except BrainfuckParseError as e:
        logging.error(f"Failed to parse code in file {filename}: {e}")
        return False

    context = BrainfuckExecutionContext(TAPE_SIZE)
    try:
        brainfuck_execute(instructions, context)
    except BrainfuckRuntimeError as e:
        logging.error(f"Runtime error in file {filename}: {e}")
        return False

    return True

def run_code(code: str) -> bool:
    """
    Executes Brainfuck code provided as a raw string.
    
    Args:
        code (str): The Brainfuck code.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        instructions = parse_string(code)
    except BrainfuckParseError as e:
        logging.error(f"Failed to parse code: {e}")
        return False

    context = BrainfuckExecutionContext(TAPE_SIZE)
    try:
        brainfuck_execute(instructions, context)
    except BrainfuckRuntimeError as e:
        logging.error(f"Runtime error: {e}")
        return False

    return True

def run_interactive_console() -> None:
    """
    Runs an interactive Brainfuck console.
    """
    print(f"Brainfuck Interpreter v{__version__} (Python)")
    print("Enter Brainfuck code (Ctrl-D to exit)")
    context = BrainfuckExecutionContext(TAPE_SIZE)
    while True:
        try:
            line = input(">> ")
        except EOFError:
            break
        if not line.strip():
            continue
        try:
            instructions = parse_string(line)
            brainfuck_execute(instructions, context)
        except (BrainfuckParseError, BrainfuckRuntimeError) as e:
            logging.error(e)
        print()

# -----------------------------------------------------------------------------
# CLI and Main Entry Point
# -----------------------------------------------------------------------------
def print_usage(progname: str) -> None:
    print(f"usage: {progname} [options] [code or file ...]", file=sys.stderr)
    print("\nIf an argument ends with .bf, it is read as a file; otherwise, it is treated as raw Brainfuck code.", file=sys.stderr)
    print("\nOptions:", file=sys.stderr)
    print("  -v, --version    show version information", file=sys.stderr)
    print("  -h, --help       show this help message", file=sys.stderr)

def print_version() -> None:
    print(f"Brainfuck Interpreter v{__version__} (Python)", file=sys.stderr)
    print("Copyright (c) 2025 Max Base.", file=sys.stderr)
    print("Distributed under the MIT License.", file=sys.stderr)

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Brainfuck Interpreter in Python",
        epilog="If an argument ends with .bf, it is read as a file; otherwise, it is treated as raw Brainfuck code.",
        add_help=False
    )
    parser.add_argument("args", nargs="*", help="Brainfuck code or file(s) to run")
    parser.add_argument("-v", "--version", action="store_true", help="show version information")
    parser.add_argument("-h", "--help", action="store_true", help="show help message")
    parsed = parser.parse_args()

    if parsed.help:
        print_usage(os.path.basename(sys.argv[0]))
        sys.exit(0)
    if parsed.version:
        print_version()
        sys.exit(0)

    if parsed.args:
        success = True
        for arg in parsed.args:
            if arg.lower().endswith(".bf"):
                if not run_file(arg):
                    logging.error(f"Failed to run file {arg}")
                    success = False
            else:
                if not run_code(arg):
                    logging.error("Failed to run code input")
                    success = False
        sys.exit(0 if success else 1)
    else:
        if not sys.stdin.isatty():
            code = sys.stdin.read()
            if not run_code(code):
                logging.error("Failed to run piped code")
                sys.exit(1)
        else:
            run_interactive_console()

if __name__ == '__main__':
    main()
