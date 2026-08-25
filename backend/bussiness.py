def get_data():
    with open('names.txt') as file:
        names = file.read()
        names = names.split()
    return names