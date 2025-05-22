from fastapi import FastAPI, HTTPException
from datetime import date, datetime
import math

app = FastAPI()


@app.get("/")
async def root():
    """
    A simple function that serves as the root endpoint for the FastAPI application.
    No parameters are passed into the function.
    Returns a dictionary with a welcome message.
    """
    return {"message": "Welcome to the FastAPI application!"}


@app.get("/current-date")
async def current_date():
    """
    Get the current date as an ISO-formatted string.
    """
    return {"date": date.today().isoformat()}


@app.get("/add/{num1}/{num2}")
async def add(num1: int, num2: int):
    """
    An asynchronous function that takes two integer parameters 'num1' and 'num2', and returns a dictionary containing the result of adding 'num1' and 'num2' under the key 'result'.
    """
    return {"result": num1 + num2}


@app.get("/subtract/{num1}/{num2}")
async def subtract(num1: int, num2: int):
    """
    A function that subtracts two numbers and returns the result as a dictionary.

    Parameters:
        num1 (int): The first number to be subtracted.
        num2 (int): The second number to subtract from the first.

    Returns:
        dict: A dictionary containing the result of the subtraction.
    """
    return {"result": num1 - num2}


@app.get("/multiply/{num1}/{num2}")
async def multiply(num1: int, num2: int):
    """
    Multiply two numbers and return the result as a dictionary.

    Parameters:
    - num1 (int): The first number to be multiplied.
    - num2 (int): The second number to be multiplied.

    Returns:
    - dict: A dictionary containing the result of the multiplication.
    """
    return {"result": num1 * num2}


@app.get("/divide/{num1}/{num2}")
async def divide(num1: int, num2: int):
    """
    An asynchronous function that handles a GET request to divide two numbers.
    Parameters:
    - num1: an integer representing the numerator
    - num2: an integer representing the denominator
    Returns:
    - A dictionary containing the result of the division
    Raises:
    - HTTPException with status code 400 if num2 is 0
    """
    if num2 == 0:
        raise HTTPException(status_code=400, detail="Cannot divide by zero")
    return {"result": num1 / num2}


@app.get("/square/{number}")
async def square(number: int):
    """
    Return the square of a number.
    """
    return {"result": number**2}


@app.get("/sqrt/{number}")
async def sqrt(number: float):
    """
    Return the square root of a number. Returns an error for negative numbers.
    """
    if number < 0:
        raise HTTPException(
            status_code=400, detail="Cannot take square root of a negative number"
        )
    return {"result": math.sqrt(number)}


@app.get("/is-palindrome/{text}")
async def is_palindrome(text: str):
    """
    Check if a string is a palindrome.
    """
    return {"is_palindrome": text == text[::-1]}


@app.get("/days-until-new-year")
async def days_until_new_year():
    """
    Calculates the number of days until the next New Year.
    """
    today = date.today()
    next_new_year = date(today.year + 1, 1, 1)
    delta = next_new_year - today
    return {"days_until_new_year": delta.days}


@app.get("/echo/{message}")
async def echo(message: str):
    """
    Returns the same message that is sent to it.
    """
    return {"message": message}
