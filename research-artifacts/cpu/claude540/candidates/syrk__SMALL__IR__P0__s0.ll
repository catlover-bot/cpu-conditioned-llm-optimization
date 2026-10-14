; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_syrk(i32 noundef %n, i32 noundef %m, double noundef %alpha, double noundef %beta, ptr noundef %C, ptr noundef %A) #0 {
entry:
  %cmp_n = icmp sgt i32 %n, 0
  br i1 %cmp_n, label %outer.preheader, label %for.end38

outer.preheader:
  %n64 = sext i32 %n to i64
  %m64 = sext i32 %m to i64
  br label %for.cond

for.cond:                                         ; preds = %for.inc36, %outer.preheader
  %i = phi i32 [ 0, %outer.preheader ], [ %inc37, %for.inc36 ]
  %i64 = sext i32 %i to i64
  %crow_off = mul nsw i64 %i64, %n64
  %crow = getelementptr inbounds double, ptr %C, i64 %crow_off
  %arow_off = mul nsw i64 %i64, %m64
  %arow = getelementptr inbounds double, ptr %A, i64 %arow_off

  ; inner loop 1: j from 0 to i inclusive
  %jub1 = add nsw i32 %i, 1
  %jcnt1_64 = sext i32 %jub1 to i64
  br label %for.body6.loop

for.body6.loop:
  %j1 = phi i64 [ 0, %for.cond ], [ %j1.next, %for.body6.loop ]
  %cptr1 = getelementptr inbounds double, ptr %crow, i64 %j1
  %cval1 = load double, ptr %cptr1, align 8
  %mul = fmul double %cval1, %beta
  store double %mul, ptr %cptr1, align 8
  %j1.next = add nuw nsw i64 %j1, 1
  %cmp1 = icmp slt i64 %j1.next, %jcnt1_64
  br i1 %cmp1, label %for.body6.loop, label %for.end

for.end:                                          ; preds = %for.body6.loop
  %cmp_m = icmp sgt i32 %m, 0
  br i1 %cmp_m, label %for.cond9.preheader, label %for.end35

for.cond9.preheader:
  br label %for.cond9

for.cond9:                                        ; preds = %for.inc33, %for.cond9.preheader
  %k = phi i32 [ 0, %for.cond9.preheader ], [ %inc34, %for.inc33 ]
  %k64 = sext i32 %k to i64

  %aik.ptr = getelementptr inbounds double, ptr %arow, i64 %k64
  %aik = load double, ptr %aik.ptr, align 8
  %alpha_aik = fmul double %alpha, %aik

  br label %for.body14.loop

for.body14.loop:
  %j2 = phi i64 [ 0, %for.cond9 ], [ %j2.next, %for.body14.loop ]
  %ajrow_off = mul nsw i64 %j2, %m64
  %ajrow = getelementptr inbounds double, ptr %A, i64 %ajrow_off
  %ajk.ptr = getelementptr inbounds double, ptr %ajrow, i64 %k64
  %ajk = load double, ptr %ajk.ptr, align 8
  %mul24 = fmul double %alpha_aik, %ajk
  %cptr2 = getelementptr inbounds double, ptr %crow, i64 %j2
  %cval2 = load double, ptr %cptr2, align 8
  %add29 = fadd double %cval2, %mul24
  store double %add29, ptr %cptr2, align 8
  %j2.next = add nuw nsw i64 %j2, 1
  %cmp2 = icmp slt i64 %j2.next, %jcnt1_64
  br i1 %cmp2, label %for.body14.loop, label %for.end32

for.end32:                                        ; preds = %for.body14.loop
  br label %for.inc33

for.inc33:                                        ; preds = %for.end32
  %inc34 = add nsw i32 %k, 1
  %cmp10 = icmp slt i32 %inc34, %m
  br i1 %cmp10, label %for.cond9, label %for.end35.loopexit

for.end35.loopexit:
  br label %for.end35

for.end35:                                        ; preds = %for.end35.loopexit, %for.end
  br label %for.inc36

for.inc36:                                        ; preds = %for.end35
  %inc37 = add nsw i32 %i, 1
  %cmp = icmp slt i32 %inc37, %n
  br i1 %cmp, label %for.cond, label %for.end38.loopexit

for.end38.loopexit:
  br label %for.end38

for.end38:                                        ; preds = %for.end38.loopexit, %entry
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
