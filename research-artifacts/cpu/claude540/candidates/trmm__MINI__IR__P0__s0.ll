; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_trmm(i32 noundef %m, i32 noundef %n, double noundef %alpha, ptr noundef %A, ptr noundef %B) #0 {
entry:
  %cmp.m = icmp sgt i32 %m, 0
  br i1 %cmp.m, label %n.check, label %for.end36

n.check:
  %cmp.n = icmp sgt i32 %n, 0
  br i1 %cmp.n, label %preheader, label %for.end36

preheader:
  %m64 = sext i32 %m to i64
  %n64 = sext i32 %n to i64
  br label %for.cond

for.cond:                                         ; preds = %for.inc34, %preheader
  %i = phi i32 [ 0, %preheader ], [ %inc35, %for.inc34 ]
  %i64 = sext i32 %i to i64
  %kstart = add nsw i32 %i, 1
  %kstart64 = sext i32 %kstart to i64
  ; Bi = &B[i*n]
  %Bi.off = mul nsw i64 %i64, %n64
  %Bi = getelementptr inbounds double, ptr %B, i64 %Bi.off
  br label %for.body

for.body:                                         ; preds = %for.inc31, %for.cond
  %j = phi i32 [ 0, %for.cond ], [ %inc32, %for.inc31 ]
  %j64 = sext i32 %j to i64
  %cmp9.pre = icmp slt i32 %kstart, %m
  br i1 %cmp9.pre, label %for.body10.preheader, label %for.end

for.body10.preheader:
  br label %for.body10

for.body10:                                       ; preds = %for.body10.preheader, %for.inc
  %k = phi i32 [ %kstart, %for.body10.preheader ], [ %inc, %for.inc ]
  %k64 = phi i64 [ %kstart64, %for.body10.preheader ], [ %k64next, %for.inc ]
  %acc = phi double [ 0.0, %for.body10.preheader ], [ %add21, %for.inc ]
  ; A[k*m + i]
  %Ak.off = mul nsw i64 %k64, %m64
  %Aidx = add nsw i64 %Ak.off, %i64
  %Aptr = getelementptr inbounds double, ptr %A, i64 %Aidx
  %Aval = load double, ptr %Aptr, align 8
  ; B[k*n + j]
  %Bk.off = mul nsw i64 %k64, %n64
  %Bkj = add nsw i64 %Bk.off, %j64
  %Bkjptr = getelementptr inbounds double, ptr %B, i64 %Bkj
  %Bkval = load double, ptr %Bkjptr, align 8
  %mul = fmul double %Aval, %Bkval
  %add21 = fadd double %acc, %mul
  br label %for.inc

for.inc:                                          ; preds = %for.body10
  %inc = add nsw i32 %k, 1
  %k64next = add nsw i64 %k64, 1
  %cmp9 = icmp slt i32 %inc, %m
  br i1 %cmp9, label %for.body10, label %for.end.loopexit

for.end.loopexit:
  %acc.lcssa = phi double [ %add21, %for.inc ]
  br label %for.end

for.end:                                          ; preds = %for.end.loopexit, %for.body
  %sum = phi double [ 0.0, %for.body ], [ %acc.lcssa, %for.end.loopexit ]
  %Bij.off = add nsw i64 %Bi.off, %j64
  %Bijptr = getelementptr inbounds double, ptr %B, i64 %Bij.off
  %mul26 = fmul double %alpha, %sum
  store double %mul26, ptr %Bijptr, align 8
  br label %for.inc31

for.inc31:                                        ; preds = %for.end
  %inc32 = add nsw i32 %j, 1
  %cmp5 = icmp slt i32 %inc32, %n
  br i1 %cmp5, label %for.body, label %for.end33

for.end33:                                        ; preds = %for.inc31
  br label %for.inc34

for.inc34:                                        ; preds = %for.end33
  %inc35 = add nsw i32 %i, 1
  %cmp = icmp slt i32 %inc35, %m
  br i1 %cmp, label %for.cond, label %for.end36.loopexit

for.end36.loopexit:
  br label %for.end36

for.end36:                                        ; preds = %for.end36.loopexit, %n.check, %entry
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
