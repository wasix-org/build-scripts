import numpy as np

# Create a 1D array
a = np.array([1, 2, 3, 4, 5])
print("1D array a:", a)

# Create a 2D array
b = np.array([[1, 2, 3], [4, 5, 6]])
print("\n2D array b:\n", b)

# Array arithmetic
print("\na + 10:", a + 10)
print("a * 2:", a * 2)

# Element-wise operations
c = np.array([5, 4, 3, 2, 1])
print("\na + c:", a + c)
print("a * c:", a * c)

# Statistical operations
print("\nMean of a:", np.mean(a))
print("Standard deviation of a:", np.std(a))

# Matrix multiplication
d = np.array([[1, 2], [3, 4]])
e = np.array([[5, 6], [7, 8]])
print("\nMatrix multiplication d @ e:\n", d @ e)

# Reshape array
f = np.arange(12).reshape(3, 4)
print("\nReshaped array f (3x4):\n", f)

# Boolean indexing
print("\nElements in a > 2:", a[a > 2])