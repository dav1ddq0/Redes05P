import errors_algs
handler = None

def add_more_zeros(data:str):
        # devuelve el reste que deja el multiplo de 8 (8q) mas cercano al len de data que es >= que len(data)
        near_mul = lambda pow8, number : pow8% number if pow8 > number else near_mul(pow8+8, number)
        for i in range(near_mul(8, len(data))):
            data = '0' +data
        return data

# convert a hexadecial data to binary '08'
def setup_data(data):
    databin = format(int(data, base = 16), '08b')
    return  add_more_zeros(databin) 

# return a frame from a valid mac ori mac des data
def get_frame(destiny_mac, origin_mac, data):
    if handler.error_detection == 'crc':
        encode = add_more_zeros(format(int(errors_algs.CRCEncode(data), base = 2), '08b'))
    else:
        _,redundant_bits_amount = errors_algs.hamming_encode(data)
        encode = add_more_zeros(format(redundant_bits_amount, '08b'))
    data_frame = format(int(destiny_mac, base = 16), '016b') + format(int(origin_mac, base=16), '016b') + format(len(data)//8, '08b') + format(len(encode)//8, '08b') + data + encode
    return data_frame


# return data from a frame
def get_data_from_frame(frame:str):
    nsizebits = int(frame[32:40], 2) * 8 # size in bytes 8*size = size en bits
    data = frame[48:48+nsizebits]
    return data

# return destiny mac from frame
def get_hex_des_mac_from_frame(frame:str):
    return bin_to_hex(frame[0:16])

# return origin mac from a frame
def get_hex_ori_mac_from_frame(frame:str):
    return bin_to_hex(frame[16:32])

# convert from binary to hexadecimal
def bin_to_hex(data):
    return '{:X}'.format(int(data,2))