from Crypto import Random

def gen_lbl():
    '''
    Generate a new Label.
    '''

    rpool =  Random.new()
    Random.atfork() 
    return rpool.read(16).encode("hex")
