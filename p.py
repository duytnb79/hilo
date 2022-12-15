

import numpy as np


def argmax_lesser_than_thresh(a, n):
    m = A<n
    m2 = m.copy()
    s = np.ones(m.sum(), dtype=bool)
    s[A[m].argmax()] = False
    m2[m] = s
    return (m2!=m)

arr = np.array([1,2,3,4,8,9,7,8,6,4,115,4,3,144,13,14,15])
A = arr
n =7 
print(arr)
a = np.where(A > n)[0][0]

print(a)
print(arr[a])

b = np.argmax(arr <= 7  )
print(b)
print(arr[b])

print()
# c = np.nanargmax(np.where(new_arr<7,new_arr,-1))

c = np.where(A < n)[0][-1]

print(c)
print(A[c])