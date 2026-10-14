; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_syrk(i32 noundef %n, i32 noundef %m, double noundef %alpha, double noundef %beta, ptr noundef %C, ptr noundef %A) #0 {
entry:
  %n64 = sext i32 %n to i64
  %m64 = sext i32 %m to i64
  %cmp.n = icmp sgt i32 %n, 0
  br i1 %cmp.n, label %outer.preheader, label %for.end38

outer.preheader:
  br label %for.cond

for.cond:                                         ; preds = %for.inc36, %outer.preheader
  %i = phi i32 [ 0, %outer.preheader ], [ %inc37, %for.inc36 ]
  %i64 = sext i32 %i to i64
  %ip1 = add nsw i32 %i, 1
  %cmp.j1 = icmp sgt i32 %ip1, 0
  %Crow.base = mul nsw i64 %i64, %n64
  %Crow.ptr = getelementptr inbounds double, ptr %C, i64 %Crow.base

  br i1 %cmp.j1, label %loop1.preheader, label %for.end

loop1.preheader:
  br label %loop1

loop1:                                            ; preds = %loop1, %loop1.preheader
  %j1 = phi i32 [ 0, %loop1.preheader ], [ %inc.j1, %loop1 ]
  %j164 = sext i32 %j1 to i64
  %arrayidx8 = getelementptr inbounds double, ptr %Crow.ptr, i64 %j164
  %ld1 = load double, ptr %arrayidx8, align 8
  %mul = fmul double %ld1, %beta
  store double %mul, ptr %arrayidx8, align 8
  %inc.j1 = add nsw i32 %j1, 1
  %cmp.j1.cond = icmp slt i32 %inc.j1, %ip1
  br i1 %cmp.j1.cond, label %loop1, label %for.end.loopexit

for.end.loopexit:
  br label %for.end

for.end:                                          ; preds = %for.end.loopexit, %for.cond
  %cmp.k = icmp sgt i32 %m, 0
  br i1 %cmp.k, label %loop2.preheader, label %for.end35

loop2.preheader:
  br label %for.cond9

for.cond9:                                        ; preds = %for.inc33, %loop2.preheader
  %k = phi i32 [ 0, %loop2.preheader ], [ %inc34, %for.inc33 ]
  %k64 = sext i32 %k to i64

  %Arow.i.base = mul nsw i64 %i64, %m64
  %Arow.i.ptr = getelementptr inbounds double, ptr %A, i64 %Arow.i.base
  %Aik.ptr = getelementptr inbounds double, ptr %Arow.i.ptr, i64 %k64
  %Aik.val = load double, ptr %Aik.ptr, align 8
  %alpha.Aik = fmul double %alpha, %Aik.val

  br i1 %cmp.j1, label %loop3.preheader, label %for.end32

loop3.preheader:
  br label %loop3

loop3:                                            ; preds = %loop3, %loop3.preheader
  %j3 = phi i32 [ 0, %loop3.preheader ], [ %inc.j3, %loop3 ]
  %j364 = sext i32 %j3 to i64

  %Arow.j.base = mul nsw i64 %j364, %m64
  %Arow.j.ptr = getelementptr inbounds double, ptr %A, i64 %Arow.j.base
  %Ajk.ptr = getelementptr inbounds double, ptr %Arow.j.ptr, i64 %k64
  %Ajk.val = load double, ptr %Ajk.ptr, align 8

  %mul24 = fmul double %alpha.Aik, %Ajk.val

  %Cij.ptr = getelementptr inbounds double, ptr %Crow.ptr, i64 %j364
  %Cij.val = load double, ptr %Cij.ptr, align 8
  %add29 = fadd double %Cij.val, %mul24
  store double %add29, ptr %Cij.ptr, align 8

  %inc.j3 = add nsw i32 %j3, 1
  %cmp.j3.cond = icmp slt i32 %inc.j3, %ip1
  br i1 %cmp.j3.cond, label %loop3, label %for.end32.loopexit

for.end32.loopexit:
  br label %for.end32

for.end32:                                        ; preds = %for.end32.loopexit, %for.cond9
  br label %for.inc33

for.inc33:                                        ; preds = %for.end32
  %inc34 = add nsw i32 %k, 1
  %cmp.k.cond = icmp slt i32 %inc34, %m
  br i1 %cmp.k.cond, label %for.cond9, label %for.end35.loopexit

for.end35.loopexit:
  br label %for.end35

for.end35:                                        ; preds = %for.end35.loopexit, %for.end
  br label %for.inc36

for.inc36:                                        ; preds = %for.end35
  %inc37 = add nsw i32 %i, 1
  %cmp.i.cond = icmp slt i32 %inc37, %n
  br i1 %cmp.i.cond, label %for.cond, label %for.end38.loopexit

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
!6 = distinct !{!6, !7}
!7 = !{!"llvm.loop.mustprogress"}
!8 = distinct !{!8, !7}
!9 = distinct !{!9, !7}
!10 = distinct !{!10, !7}
