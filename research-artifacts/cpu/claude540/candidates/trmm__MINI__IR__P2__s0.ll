; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_trmm(i32 noundef %m, i32 noundef %n, double noundef %alpha, ptr noundef %A, ptr noundef %B) #0 {
entry:
  %cmp_mn = icmp sgt i32 %m, 0
  %cmp_nn = icmp sgt i32 %n, 0
  %run = and i1 %cmp_mn, %cmp_nn
  br i1 %run, label %preheader, label %for.end36

preheader:
  %m64 = sext i32 %m to i64
  %n64 = sext i32 %n to i64
  br label %for.i

for.i:                                            ; preds = %for.inc34, %preheader
  %i = phi i64 [ 0, %preheader ], [ %inc35, %for.inc34 ]

  ; k range for this i: [i+1, m)
  %kstart = add nsw i64 %i, 1
  %khasany = icmp slt i64 %kstart, %m64

  ; A row base for column i: A + k*m + i handled per-k below
  br label %for.j

for.j:                                            ; preds = %for.inc31, %for.i
  %j = phi i64 [ 0, %for.i ], [ %inc32, %for.inc31 ]

  %Bij_ptr0 = getelementptr inbounds double, ptr %B, i64 %i
  %irow_off = mul nsw i64 %i, %n64
  %Bij_ptr = getelementptr inbounds double, ptr %B, i64 %irow_off
  %Bij_ptr2 = getelementptr inbounds double, ptr %Bij_ptr, i64 %j

  br i1 %khasany, label %for.k.preheader, label %for.end

for.k.preheader:
  br label %for.k

for.k:                                            ; preds = %for.k.preheader, %for.k
  %k = phi i64 [ %kstart, %for.k.preheader ], [ %inc, %for.k ]
  %acc = phi double [ 0.000000e+00, %for.k.preheader ], [ %add21, %for.k ]

  %koff = mul nsw i64 %k, %m64
  %Aoff = add nsw i64 %koff, %i
  %Aptr = getelementptr inbounds double, ptr %A, i64 %Aoff
  %Aval = load double, ptr %Aptr, align 8

  %Bkoff = mul nsw i64 %k, %n64
  %Bkoff2 = add nsw i64 %Bkoff, %j
  %Bkptr = getelementptr inbounds double, ptr %B, i64 %Bkoff2
  %Bval = load double, ptr %Bkptr, align 8

  %mul = fmul double %Aval, %Bval
  %add21 = fadd double %acc, %mul

  %inc = add nsw i64 %k, 1
  %kcmp = icmp slt i64 %inc, %m64
  br i1 %kcmp, label %for.k, label %for.k.exit

for.k.exit:
  br label %for.end

for.end:                                          ; preds = %for.k.exit, %for.j
  %sum = phi double [ 0.000000e+00, %for.j ], [ %add21, %for.k.exit ]

  ; Now perform: Bij = alpha * (Bij + sum)  -- but original does two separate steps:
  ; first accumulate sum into B[i][j] via the k loop (each iter reads/writes B[i][j]),
  ; but since sum is computed independently across k without reading B until we add,
  ; original code actually does: B[i][j] = B[i][j] + A[k][i]*B[k][j] repeatedly for each k.
  ; That means original updates B[i][j] incrementally, equivalent to B[i][j] += sum(A[k][i]*B[k][j])
  ; since B[i][j] itself is never read as part of the k-loop's multiplicand (k starts at i+1, so B[k][j] with k>i doesn't alias B[i][j]).
  ; So final B[i][j] after k-loop = original_Bij + sum. Then alpha multiply.
  %Bij_orig = load double, ptr %Bij_ptr2, align 8
  %Bij_plus = fadd double %Bij_orig, %sum
  %res = fmul double %alpha, %Bij_plus
  store double %res, ptr %Bij_ptr2, align 8

  br label %for.inc31

for.inc31:                                        ; preds = %for.end
  %inc32 = add nsw i64 %j, 1
  %jcmp = icmp slt i64 %inc32, %n64
  br i1 %jcmp, label %for.j, label %for.j.exit

for.j.exit:
  br label %for.inc34

for.inc34:                                        ; preds = %for.j.exit
  %inc35 = add nsw i64 %i, 1
  %icmp2 = icmp slt i64 %inc35, %m64
  br i1 %icmp2, label %for.i, label %for.end36

for.end36:                                        ; preds = %for.inc34, %entry
  ret void
}

attributes #0 = { noinline nounwind uwtable "frame-pointer"="all" "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" }

!llvm.module.flags = !{!0, !1, !2, !3, !4}
!llvm.ident = !{!5}

!0 = !{i32 1, !"wchar_size", i32 4}
!1 = !{i32 8, !"PIC Level", i32 2}
!2 = !{i32 7, !"PIE Level", i32 2}
!3 = !{i32 7, !"uwtable", i32 2}
!4 = !{i32 7, !"frame-pointer", i32 2}
!5 = !{!"Ubuntu clang version 18.1.3 (1ubuntu1)"}
