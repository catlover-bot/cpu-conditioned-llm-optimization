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
  %yptr0 = getelementptr inbounds double, ptr %y, i64 %iv0
  store double 0.000000e+00, ptr %yptr0, align 8
  %iv0.next = add nuw nsw i64 %iv0, 1
  %cmp0 = icmp slt i64 %iv0.next, %n64
  br i1 %cmp0, label %init.y, label %for.end

for.end:
  %cmp.m = icmp sgt i32 %m, 0
  br i1 %cmp.m, label %outer.preheader, label %for.end47

outer.preheader:
  %m64 = zext i32 %m to i64
  %n64b = zext i32 %n to i64
  %n.pos = icmp sgt i32 %n, 0
  br label %outer

outer:
  %i = phi i64 [ 0, %outer.preheader ], [ %i.next, %outer.latch ]
  %tmpi.ptr = getelementptr inbounds double, ptr %tmp, i64 %i
  store double 0.000000e+00, ptr %tmpi.ptr, align 8
  %Arow.offset = mul nsw i64 %i, %n64b
  %Arow = getelementptr inbounds double, ptr %A, i64 %Arow.offset
  br i1 %n.pos, label %inner1.preheader, label %inner1.end

inner1.preheader:
  br label %inner1

inner1:
  %j1 = phi i64 [ 0, %inner1.preheader ], [ %j1.next, %inner1 ]
  %tval = phi double [ 0.000000e+00, %inner1.preheader ], [ %add21, %inner1 ]
  %Aij1 = getelementptr inbounds double, ptr %Arow, i64 %j1
  %a1 = load double, ptr %Aij1, align 8
  %xj1 = getelementptr inbounds double, ptr %x, i64 %j1
  %xv1 = load double, ptr %xj1, align 8
  %mul1 = fmul double %a1, %xv1
  %add21 = fadd double %tval, %mul1
  %j1.next = add nuw nsw i64 %j1, 1
  %cmp1 = icmp slt i64 %j1.next, %n64b
  br i1 %cmp1, label %inner1, label %inner1.exit

inner1.exit:
  store double %add21, ptr %tmpi.ptr, align 8
  br label %inner1.end

inner1.end:
  %tmp.val = phi double [ %add21, %inner1.exit ], [ 0.000000e+00, %outer ]
  br i1 %n.pos, label %inner2.preheader, label %outer.latch

inner2.preheader:
  br label %inner2

inner2:
  %j2 = phi i64 [ 0, %inner2.preheader ], [ %j2.next, %inner2 ]
  %Aij2 = getelementptr inbounds double, ptr %Arow, i64 %j2
  %a2 = load double, ptr %Aij2, align 8
  %yj2 = getelementptr inbounds double, ptr %y, i64 %j2
  %yv2 = load double, ptr %yj2, align 8
  %mul2 = fmul double %a2, %tmp.val
  %add39 = fadd double %yv2, %mul2
  store double %add39, ptr %yj2, align 8
  %j2.next = add nuw nsw i64 %j2, 1
  %cmp2 = icmp slt i64 %j2.next, %n64b
  br i1 %cmp2, label %inner2, label %outer.latch

outer.latch:
  %i.next = add nuw nsw i64 %i, 1
  %cmp.outer = icmp slt i64 %i.next, %m64
  br i1 %cmp.outer, label %outer, label %for.end47

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
