import sqlite3

def connect_data():
    return sqlite3.connect("banco.db")