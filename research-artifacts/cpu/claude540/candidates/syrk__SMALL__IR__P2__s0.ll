; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_syrk(i32 noundef %n, i32 noundef %m, double noundef %alpha, double noundef %beta, ptr noundef %C, ptr noundef %A) #0 {
entry:
  %n64 = sext i32 %n to i64
  %m64 = sext i32 %m to i64

  %ncmp = icmp sgt i32 %n, 0
  br i1 %ncmp, label %outer.preheader, label %for.end38

outer.preheader:
  br label %for.body

for.body:                                         ; preds = %for.inc36, %outer.preheader
  %i = phi i32 [ 0, %outer.preheader ], [ %inc37, %for.inc36 ]
  %i64 = sext i32 %i to i64
  %crow.off = mul nsw i64 %i64, %n64
  %crow.ptr = getelementptr inbounds double, ptr %C, i64 %crow.off
  %arow.off = mul nsw i64 %i64, %m64
  %arow.ptr = getelementptr inbounds double, ptr %A, i64 %arow.off

  ; inner loop 1: for (j = 0; j <= i; j++) C[i][j] *= beta;
  %jcount1 = add nsw i32 %i, 1
  br label %loop1.body

loop1.body:                                       ; preds = %loop1.body, %for.body
  %j1 = phi i32 [ 0, %for.body ], [ %j1.next, %loop1.body ]
  %j1_64 = sext i32 %j1 to i64
  %cptr1 = getelementptr inbounds double, ptr %crow.ptr, i64 %j1_64
  %cval1 = load double, ptr %cptr1, align 8
  %mul1 = fmul double %cval1, %beta
  store double %mul1, ptr %cptr1, align 8
  %j1.next = add nsw i32 %j1, 1
  %cmp1 = icmp slt i32 %j1.next, %jcount1
  br i1 %cmp1, label %loop1.body, label %for.end

for.end:                                          ; preds = %loop1.body
  %mcmp = icmp sgt i32 %m, 0
  br i1 %mcmp, label %k.preheader, label %for.end35

k.preheader:
  br label %for.body11

for.body11:                                       ; preds = %for.inc33, %k.preheader
  %k = phi i32 [ 0, %k.preheader ], [ %inc34, %for.inc33 ]
  %k64 = sext i32 %k to i64
  %aik.ptr = getelementptr inbounds double, ptr %arow.ptr, i64 %k64
  %aik = load double, ptr %aik.ptr, align 8
  %alpha_aik = fmul double %alpha, %aik

  ; inner loop: for (j = 0; j <= i; j++) C[i][j] += alpha*A[i][k]*A[j][k];
  %jcount2 = add nsw i32 %i, 1
  br label %loop2.body

loop2.body:                                       ; preds = %loop2.body, %for.body11
  %j2 = phi i32 [ 0, %for.body11 ], [ %j2.next, %loop2.body ]
  %j2_64 = sext i32 %j2 to i64
  %arow2.off = mul nsw i64 %j2_64, %m64
  %ajk.ptr = getelementptr inbounds double, ptr %A, i64 %arow2.off
  %ajk.ptr2 = getelementptr inbounds double, ptr %ajk.ptr, i64 %k64
  %ajk = load double, ptr %ajk.ptr2, align 8
  %mul24 = fmul double %alpha_aik, %ajk
  %cptr2 = getelementptr inbounds double, ptr %crow.ptr, i64 %j2_64
  %cval2 = load double, ptr %cptr2, align 8
  %add29 = fadd double %cval2, %mul24
  store double %add29, ptr %cptr2, align 8
  %j2.next = add nsw i32 %j2, 1
  %cmp2 = icmp slt i32 %j2.next, %jcount2
  br i1 %cmp2, label %loop2.body, label %for.inc33

for.inc33:                                        ; preds = %loop2.body
  %inc34 = add nsw i32 %k, 1
  %cmpk = icmp slt i32 %inc34, %m
  br i1 %cmpk, label %for.body11, label %for.end35

for.end35:                                        ; preds = %for.inc33, %for.end
  br label %for.inc36

for.inc36:                                        ; preds = %for.end35
  %inc37 = add nsw i32 %i, 1
  %cmpi = icmp slt i32 %inc37, %n
  br i1 %cmpi, label %for.body, label %for.end38

for.end38:                                        ; preds = %for.inc36, %entry
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
