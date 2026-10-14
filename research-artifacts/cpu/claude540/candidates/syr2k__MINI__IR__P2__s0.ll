; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_syr2k(i32 noundef %n, i32 noundef %m, double noundef %alpha, double noundef %beta, ptr noundef %C, ptr noundef %A, ptr noundef %B) #0 {
entry:
  %n64 = sext i32 %n to i64
  %m64 = sext i32 %m to i64

  %ncmp = icmp sgt i32 %n, 0
  br i1 %ncmp, label %outer.preheader, label %for.end51

outer.preheader:
  br label %for.cond

for.cond:                                         ; preds = %for.inc49, %outer.preheader
  %i = phi i32 [ 0, %outer.preheader ], [ %inc50, %for.inc49 ]
  %i64 = sext i32 %i to i64
  %crow.off = mul nsw i64 %i64, %n64
  %crow = getelementptr inbounds double, ptr %C, i64 %crow.off
  %arow.off = mul nsw i64 %i64, %m64
  %arow = getelementptr inbounds double, ptr %A, i64 %arow.off
  %brow = getelementptr inbounds double, ptr %B, i64 %arow.off

  ; first inner loop: j from 0 to i (inclusive), scale C
  %jcount1_64 = add nsw i64 %i64, 1
  %jcount1 = trunc i64 %jcount1_64 to i32
  br label %for.body8.preheader

for.body8.preheader:
  br label %for.body8

for.body8:                                        ; preds = %for.body8, %for.body8.preheader
  %j1 = phi i32 [ 0, %for.body8.preheader ], [ %inc.j1, %for.body8 ]
  %j1_64 = sext i32 %j1 to i64
  %cptr1 = getelementptr inbounds double, ptr %crow, i64 %j1_64
  %cval1 = load double, ptr %cptr1, align 8
  %cmul = fmul double %cval1, %beta
  store double %cmul, ptr %cptr1, align 8
  %inc.j1 = add nsw i32 %j1, 1
  %cmp.j1 = icmp sle i32 %inc.j1, %i
  br i1 %cmp.j1, label %for.body8, label %for.end.j1

for.end.j1:
  br label %for.end

for.end:                                          ; preds = %for.end.j1
  %mcmp = icmp sgt i32 %m, 0
  br i1 %mcmp, label %for.body13.preheader, label %for.end48

for.body13.preheader:
  br label %for.cond11

for.cond11:                                       ; preds = %for.inc46, %for.body13.preheader
  %k = phi i32 [ 0, %for.body13.preheader ], [ %inc47, %for.inc46 ]
  %k64 = sext i32 %k to i64
  %aik.ptr = getelementptr inbounds double, ptr %arow, i64 %k64
  %aik = load double, ptr %aik.ptr, align 8
  %alpha.aik = fmul double %aik, %alpha
  %bik.ptr = getelementptr inbounds double, ptr %brow, i64 %k64
  %bik = load double, ptr %bik.ptr, align 8
  %alpha.bik = fmul double %bik, %alpha

  br label %for.body16.preheader

for.body16.preheader:
  br label %for.body16

for.body16:                                       ; preds = %for.body16, %for.body16.preheader
  %j2 = phi i32 [ 0, %for.body16.preheader ], [ %inc.j2, %for.body16 ]
  %j2_64 = sext i32 %j2 to i64
  %ajk.ptr = getelementptr inbounds double, ptr %A, i64 %j2_64
  %ajk.off = mul nsw i64 %j2_64, %m64
  %ajk.ptr2 = getelementptr inbounds double, ptr %A, i64 %ajk.off
  %ajk.ptr3 = getelementptr inbounds double, ptr %ajk.ptr2, i64 %k64
  %ajk = load double, ptr %ajk.ptr3, align 8

  %bjk.off = mul nsw i64 %j2_64, %m64
  %bjk.ptr2 = getelementptr inbounds double, ptr %B, i64 %bjk.off
  %bjk.ptr3 = getelementptr inbounds double, ptr %bjk.ptr2, i64 %k64
  %bjk = load double, ptr %bjk.ptr3, align 8

  %mul26 = fmul double %alpha.aik, %bjk
  %mul36 = fmul double %alpha.bik, %ajk
  %add37 = fadd double %mul26, %mul36

  %cptr2 = getelementptr inbounds double, ptr %crow, i64 %j2_64
  %cval2 = load double, ptr %cptr2, align 8
  %add42 = fadd double %cval2, %add37
  store double %add42, ptr %cptr2, align 8

  %inc.j2 = add nsw i32 %j2, 1
  %cmp.j2 = icmp sle i32 %inc.j2, %i
  br i1 %cmp.j2, label %for.body16, label %for.end.j2

for.end.j2:
  br label %for.inc46

for.inc46:                                        ; preds = %for.end.j2
  %inc47 = add nsw i32 %k, 1
  %cmp.k = icmp slt i32 %inc47, %m
  br i1 %cmp.k, label %for.cond11, label %for.end48.loopexit

for.end48.loopexit:
  br label %for.end48

for.end48:                                        ; preds = %for.end48.loopexit, %for.end
  br label %for.inc49

for.inc49:                                        ; preds = %for.end48
  %inc50 = add nsw i32 %i, 1
  %cmp.i = icmp slt i32 %inc50, %n
  br i1 %cmp.i, label %for.cond, label %for.end51.loopexit

for.end51.loopexit:
  br label %for.end51

for.end51:                                        ; preds = %for.end51.loopexit, %entry
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
