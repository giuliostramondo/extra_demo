#include<stdio.h>

int main(int argc, char *argv[]){
int offset=5;
int skip=4;
int read=3;
int DimY= 512;
int DimX= 170;

double A[170][512];
double B[170][512];
double C[170][512];

for (int i=0;i<170;i++)
    for (int j=0;j<512;j++){
                A[i][j] = i*512+j;
                B[i][j] = i*512+j;
                C[i][j] = -1;
}

#pragma polymem in 0 0 double A[170][512]
#pragma polymem in 170 0 double B[170][512]
#pragma polymem out 340 0 double C[170][512]

#pragma polymem loop
for(int i=0;i<170;i+=1){
	for(int j=0;j<512;j+=1){
		if((i*DimY+j)>=offset && (i*DimY+j-offset)%(skip+read)<read){
			B[i][j]=A[i][j]+C[i][j];
			}
	}
}

for (int i=0;i<170;i++)
    for (int j=0;j<512;j++){
        printf("(%d %d) %f\n",i,j,C[i][j]);
    }
}
