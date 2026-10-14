; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_syrk(i32 noundef %n, i32 noundef %m, double noundef %alpha, double noundef %beta, ptr noundef %C, ptr noundef %A) #0 {
entry:
  %n64 = sext i32 %n to i64
  %m64 = sext i32 %m to i64
  %cmp.n = icmp slt i32 0, %n
  br i1 %cmp.n, label %for.outer.preheader, label %for.end38

for.outer.preheader:
  br label %for.body

for.body:                                         ; preds = %for.inc36, %for.outer.preheader
  %i = phi i32 [ 0, %for.outer.preheader ], [ %inc37, %for.inc36 ]
  %i64 = sext i32 %i to i64
  %Ci.off = mul nsw i64 %i64, %n64
  %Crow.i = getelementptr inbounds double, ptr %C, i64 %Ci.off
  %Ai.off = mul nsw i64 %i64, %m64
  %Arow.i = getelementptr inbounds double, ptr %A, i64 %Ai.off

  ; inner loop 1: j from 0 to i (inclusive), scale C[i][j] by beta
  %cmp.j1 = icmp sle i32 0, %i
  br i1 %cmp.j1, label %loop1.preheader, label %for.end

loop1.preheader:
  br label %loop1.body

loop1.body:
  %j1 = phi i32 [ 0, %loop1.preheader ], [ %inc.j1, %loop1.body ]
  %j1.64 = sext i32 %j1 to i64
  %Cij1.ptr = getelementptr inbounds double, ptr %Crow.i, i64 %j1.64
  %Cij1.val = load double, ptr %Cij1.ptr, align 8
  %Cij1.mul = fmul double %Cij1.val, %beta
  store double %Cij1.mul, ptr %Cij1.ptr, align 8
  %inc.j1 = add nsw i32 %j1, 1
  %cmp.j1.next = icmp sle i32 %inc.j1, %i
  br i1 %cmp.j1.next, label %loop1.body, label %for.end

for.end:                                          ; preds = %loop1.body, %for.body
  %cmp.k = icmp slt i32 0, %m
  br i1 %cmp.k, label %loop.k.preheader, label %for.end35

loop.k.preheader:
  br label %loop.k.body

loop.k.body:                                      ; preds = %for.inc33, %loop.k.preheader
  %k = phi i32 [ 0, %loop.k.preheader ], [ %inc34, %for.inc33 ]
  %k64 = sext i32 %k to i64

  %Aik.ptr = getelementptr inbounds double, ptr %Arow.i, i64 %k64
  %Aik.val = load double, ptr %Aik.ptr, align 8
  %alpha.Aik = fmul double %alpha, %Aik.val

  %cmp.j2 = icmp sle i32 0, %i
  br i1 %cmp.j2, label %loop2.preheader, label %for.end32

loop2.preheader:
  br label %loop2.body

loop2.body:
  %j2 = phi i32 [ 0, %loop2.preheader ], [ %inc.j2, %loop2.body ]
  %j2.64 = sext i32 %j2 to i64

  %Aj.off = mul nsw i64 %j2.64, %m64
  %Arow.j = getelementptr inbounds double, ptr %A, i64 %Aj.off
  %Ajk.ptr = getelementptr inbounds double, ptr %Arow.j, i64 %k64
  %Ajk.val = load double, ptr %Ajk.ptr, align 8

  %mul24 = fmul double %alpha.Aik, %Ajk.val

  %Cij2.ptr = getelementptr inbounds double, ptr %Crow.i, i64 %j2.64
  %Cij2.val = load double, ptr %Cij2.ptr, align 8
  %add29 = fadd double %Cij2.val, %mul24
  store double %add29, ptr %Cij2.ptr, align 8

  %inc.j2 = add nsw i32 %j2, 1
  %cmp.j2.next = icmp sle i32 %inc.j2, %i
  br i1 %cmp.j2.next, label %loop2.body, label %for.end32

for.end32:                                        ; preds = %loop2.body, %loop.k.body
  br label %for.inc33

for.inc33:                                        ; preds = %for.end32
  %inc34 = add nsw i32 %k, 1
  %cmp.k.next = icmp slt i32 %inc34, %m
  br i1 %cmp.k.next, label %loop.k.body, label %for.end35

for.end35:                                        ; preds = %for.inc33, %for.end
  br label %for.inc36

for.inc36:                                        ; preds = %for.end35
  %inc37 = add nsw i32 %i, 1
  %cmp.next = icmp slt i32 %inc37, %n
  br i1 %cmp.next, label %for.body, label %for.end38

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
