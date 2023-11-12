import numba as nb
import numpy as np

@nb.njit(fastmath=True,parallel=True)
def eucl_naive(A,B):
    assert A.shape[1]==B.shape[1]
    C=np.empty((A.shape[0],B.shape[0]),A.dtype)
    
    #workaround to get the right datatype for acc
    init_val_arr=np.zeros(1,A.dtype)
    init_val=init_val_arr[0]
    
    for i in nb.prange(A.shape[0]):
        for j in range(B.shape[0]):
            acc=init_val
            for k in range(A.shape[1]):
                acc+=(A[i,k]-B[j,k])**2
            C[i,j]=np.sqrt(acc)
    return C

@nb.njit(fastmath=True,parallel=True)
def eucl_opt(A, B):
    assert A.shape[1]==B.shape[1]
    C=np.empty((A.shape[0],B.shape[0]),A.dtype)
    I_BLK=32
    J_BLK=32
    
    #workaround to get the right datatype for acc
    init_val_arr=np.zeros(1,A.dtype)
    init_val=init_val_arr[0]
    
    #Blocking and partial unrolling
    #Beneficial if the second dimension is large -> computationally bound problem 
    # 
    for ii in nb.prange(A.shape[0]//I_BLK):
        for jj in range(B.shape[0]//J_BLK):
            for i in range(I_BLK//4):
                for j in range(J_BLK//2):
                    acc_0=init_val
                    acc_1=init_val
                    acc_2=init_val
                    acc_3=init_val
                    acc_4=init_val
                    acc_5=init_val
                    acc_6=init_val
                    acc_7=init_val
                    for k in range(A.shape[1]):
                        acc_0+=(A[ii*I_BLK+i*4+0,k] - B[jj*J_BLK+j*2+0,k])**2
                        acc_1+=(A[ii*I_BLK+i*4+0,k] - B[jj*J_BLK+j*2+1,k])**2
                        acc_2+=(A[ii*I_BLK+i*4+1,k] - B[jj*J_BLK+j*2+0,k])**2
                        acc_3+=(A[ii*I_BLK+i*4+1,k] - B[jj*J_BLK+j*2+1,k])**2
                        acc_4+=(A[ii*I_BLK+i*4+2,k] - B[jj*J_BLK+j*2+0,k])**2
                        acc_5+=(A[ii*I_BLK+i*4+2,k] - B[jj*J_BLK+j*2+1,k])**2
                        acc_6+=(A[ii*I_BLK+i*4+3,k] - B[jj*J_BLK+j*2+0,k])**2
                        acc_7+=(A[ii*I_BLK+i*4+3,k] - B[jj*J_BLK+j*2+1,k])**2
                    C[ii*I_BLK+i*4+0,jj*J_BLK+j*2+0]=np.sqrt(acc_0)
                    C[ii*I_BLK+i*4+0,jj*J_BLK+j*2+1]=np.sqrt(acc_1)
                    C[ii*I_BLK+i*4+1,jj*J_BLK+j*2+0]=np.sqrt(acc_2)
                    C[ii*I_BLK+i*4+1,jj*J_BLK+j*2+1]=np.sqrt(acc_3)
                    C[ii*I_BLK+i*4+2,jj*J_BLK+j*2+0]=np.sqrt(acc_4)
                    C[ii*I_BLK+i*4+2,jj*J_BLK+j*2+1]=np.sqrt(acc_5)
                    C[ii*I_BLK+i*4+3,jj*J_BLK+j*2+0]=np.sqrt(acc_6)
                    C[ii*I_BLK+i*4+3,jj*J_BLK+j*2+1]=np.sqrt(acc_7)
        #Remainder j
        for i in range(I_BLK):
            for j in range((B.shape[0]//J_BLK)*J_BLK,B.shape[0]):
                acc_0=init_val
                for k in range(A.shape[1]):
                    acc_0+=(A[ii*I_BLK+i,k] - B[j,k])**2
                C[ii*I_BLK+i,j]=np.sqrt(acc_0)
    
    #Remainder i
    for i in range((A.shape[0]//I_BLK)*I_BLK,A.shape[0]):
        for j in range(B.shape[0]):
            acc_0=init_val
            for k in range(A.shape[1]):
                acc_0+=(A[i,k] - B[j,k])**2
            C[i,j]=np.sqrt(acc_0)
            
    return C

@nb.njit(fastmath=True)
def eucl_BLAS(A,B):
    dist=np.dot(A,B.T)

    TMP_A=np.empty(A.shape[0],dtype=A.dtype)
    for i in range(A.shape[0]):
        sum=0
        for j in range(A.shape[1]):
            sum+=A[i,j]**2
        TMP_A[i]=sum

    TMP_B=np.empty(B.shape[0],dtype=A.dtype)
    for i in range(B.shape[0]):
        sum=0
        for j in range(B.shape[1]):
            sum+=B[i,j]**2
        TMP_B[i]=sum
    
    for i in range(A.shape[0]):
        for j in range(B.shape[0]):
            dist[i,j]=np.sqrt(-2.*dist[i,j]+TMP_A[i]+TMP_B[j])
    return dist