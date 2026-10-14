; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_atax(i32 noundef %m, i32 noundef %n, ptr noundef %A, ptr noundef %x, ptr noundef %y, ptr noundef %tmp) #0 {
entry:
  %cmp.n = icmp sgt i32 %n, 0
  br i1 %cmp.n, label %init.y.preheader, label %for.end

init.y.preheader:
  %n64 = zext i32 %n to i64
  br label %init.y

init.y:
  %iv0 = phi i64 [ 0, %init.y.preheader ], [ %iv0.next, %init.y ]
  %yp = getelementptr inbounds double, ptr %y, i64 %iv0
  store double 0.000000e+00, ptr %yp, align 8
  %iv0.next = add nuw nsw i64 %iv0, 1
  %cmp0 = icmp slt i64 %iv0.next, %n64
  br i1 %cmp0, label %init.y, label %for.end

for.end:
  %cmp.m = icmp sgt i32 %m, 0
  br i1 %cmp.m, label %outer.preheader, label %for.end47

outer.preheader:
  %n64b = zext i32 %n to i64
  %m64 = zext i32 %m to i64
  %n_gt0 = icmp sgt i32 %n, 0
  br label %outer

outer:
  %i = phi i64 [ 0, %outer.preheader ], [ %i.next, %inc45 ]
  %A.row = getelementptr inbounds double, ptr %A, i64 %i
  %Arow.ptr0 = getelementptr inbounds double, ptr %A, i64 0
  %rowoff = mul nsw i64 %i, %n64b
  %Arow = getelementptr inbounds double, ptr %A, i64 %rowoff
  %tmp.i.ptr = getelementptr inbounds double, ptr %tmp, i64 %i
  store double 0.000000e+00, ptr %tmp.i.ptr, align 8
  br i1 %n_gt0, label %inner1.preheader, label %for.end26

inner1.preheader:
  br label %inner1

inner1:
  %j1 = phi i64 [ 0, %inner1.preheader ], [ %j1.next, %inner1 ]
  %acc = phi double [ 0.000000e+00, %inner1.preheader ], [ %acc.next, %inner1 ]
  %Aij.ptr = getelementptr inbounds double, ptr %Arow, i64 %j1
  %Aij = load double, ptr %Aij.ptr, align 8
  %xj.ptr = getelementptr inbounds double, ptr %x, i64 %j1
  %xj = load double, ptr %xj.ptr, align 8
  %mul1 = fmul double %Aij, %xj
  %acc.next = fadd double %acc, %mul1
  %j1.next = add nuw nsw i64 %j1, 1
  store double %acc.next, ptr %tmp.i.ptr, align 8
  %cmp1 = icmp slt i64 %j1.next, %n64b
  br i1 %cmp1, label %inner1, label %for.end26

for.end26:
  %tmpi.val = load double, ptr %tmp.i.ptr, align 8
  br i1 %n_gt0, label %inner2.preheader, label %inc45

inner2.preheader:
  br label %inner2

inner2:
  %j2 = phi i64 [ 0, %inner2.preheader ], [ %j2.next, %inner2 ]
  %yj.ptr = getelementptr inbounds double, ptr %y, i64 %j2
  %yj = load double, ptr %yj.ptr, align 8
  %Aij2.ptr = getelementptr inbounds double, ptr %Arow, i64 %j2
  %Aij2 = load double, ptr %Aij2.ptr, align 8
  %mul2 = fmul double %Aij2, %tmpi.val
  %add2 = fadd double %yj, %mul2
  store double %add2, ptr %yj.ptr, align 8
  %j2.next = add nuw nsw i64 %j2, 1
  %cmp2 = icmp slt i64 %j2.next, %n64b
  br i1 %cmp2, label %inner2, label %inc45

inc45:
  %i.next = add nuw nsw i64 %i, 1
  %cmpo = icmp slt i64 %i.next, %m64
  br i1 %cmpo, label %outer, label %for.end47

for.end47:
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
