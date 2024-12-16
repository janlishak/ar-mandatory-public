def outer_function(msg):
    def inner_function():
        nonlocal msg
        print(msg)
        msg = msg + "something"
    return inner_function