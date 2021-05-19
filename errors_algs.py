def xor(n1, n2):
    result = []

    for i in range(1, len(n2)):
        if n1[i] == n2[i]:
            result.append('0')
        else:
            result.append('1')
    
    return ''.join(result)

crc_key = '1011'

def mod2div(divident, divisor):
    # Number of bits to be XORed at a time.
    pick = len(divisor)
    # Slicing the divident to appropriate
    # length for particular step
    tmp = divident[0 : pick]
    while pick < len(divident):
        if tmp[0] == '1':
            # replace the divident by the result
            # of XOR and pull 1 bit down
            tmp = xor(divisor, tmp) + divident[pick]
        else:   # If leftmost bit is '0'
            # If the leftmost bit of the dividend (or the
            # part used in each step) is 0, the step cannot
            # use the regular divisor; we need to use an
            # all-0s divisor.
            tmp = xor('0'*pick, tmp) + divident[pick]
        # increment pick to move further
        pick += 1
    
    if tmp[0] == '1':
        tmp = xor(divisor, tmp)
    else:
        tmp = xor('0'*pick, tmp)

    remainder = tmp
    return remainder

def CRCEncode(data):
    # x^3+x+1 representing en bin like 1 0 1 1 
    # Add n-1 zeroes at end of data where n is len of key
    l_key = len(crc_key)
    appended_data = data + '0'*(l_key-1)
    remainder = mod2div(appended_data, crc_key)
    
    return remainder    

def CRCDecode(data):
    # x^3+x+1 representing en bin like 1 0 1 1 
    # Add n-1 zeroes at end of data where n is len of key 
    remainder = mod2div(data, crc_key)
    
    return remainder

def CheckError(remainder):
    return remainder == 0


def hamming_encode(data_frame):

    frame_len = len(data_frame)
    redundant_bits_amount = 0
    for i in range(frame_len):
        if(2**i >= frame_len + i + 1):
            redundant_bits_amount = i
            break
    
    j = 0
    k = 1
    encoded_frame = ''
    # If position is power of 2 then insert '0'
    # Else append the data
    for i in range(1, frame_len + redundant_bits_amount + 1):
        if(i == 2**j):
            encoded_frame = encoded_frame + '0'
            j += 1
        else:
            encoded_frame = encoded_frame + data_frame[-1 * k]
            k += 1
    
    encoded_frame = encoded_frame[::-1]
    frame_len = len(encoded_frame)

    # For finding rth parity bit, iterate over
    # 0 to r - 1
    for i in range(redundant_bits_amount):
        val = 0
        for j in range(1, frame_len + 1):
            # If position has 1 in ith significant
            # position then Bitwise OR the array value
            # to find parity bit value.
            if(j & (2**i) == (2**i)):
                val = val ^ int(encoded_frame[-1 * j])
                # -1 * j is given since array is reversed

        # String Concatenation
        # (0 to n - 2^r) + parity bit + (n - 2^r + 1 to n)
        encoded_frame = encoded_frame[:frame_len-(2**i)] + str(val) + encoded_frame[frame_len-(2**i)+1:]

    return encoded_frame, redundant_bits_amount

def calc_error_bit_pos(encoded_data_error_bit_pos):

    i = 0
    powers = 0 #cantidad de potencias de 2 menores que encoded_data_error_bit_pos
    while 2**i < encoded_data_error_bit_pos:
        powers += 1
        i += 1

    return encoded_data_error_bit_pos - powers


def calc_redundant_bits(encoded_frame):

    j = 0
    redundant_bits = ''
    for i in range(1, len(encoded_frame)):
        if i == 2**j:
            redundant_bits = encoded_frame[-i] + redundant_bits
            j += 1

    return redundant_bits

def hamming_decode(encoded_frame):

    decoded_frame = ''  

    j = 0
    for i in range(1, len(encoded_frame) + 1):
        if(i != 2**j):
            decoded_frame += encoded_frame[-i]
        
        else : j += 1
                
    return decoded_frame[::-1]

def fix_bit(data, wrong_bit_position):
    fixed_data = ''

    for i in range(1, len(data) + 1):
        if i != wrong_bit_position:
            fixed_data = data[-i] + fixed_data
        
        else : fixed_data = '1' + fixed_data if data[-i] == '0' else '0' + fixed_data

    return fixed_data

def detect_error(encoded_frame, redundant_bits_amount):
    frame_len = len(encoded_frame)
    res = 0
    # Calculate parity bits again
    for i in range(redundant_bits_amount):
        val = 0
        for j in range(1, frame_len + 1):
            if(j & (2**i) == (2**i)):
                val = val ^ int(encoded_frame[-1 * j])
        # Create a binary no by appending
        # parity bits together.
        res = res + val*(10**i)
    # Convert binary to decimal, 0 means no error
    error_index = int(str(res), 2)
    return True if error_index else False, error_index