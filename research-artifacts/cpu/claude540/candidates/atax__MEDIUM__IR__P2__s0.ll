; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_atax(i32 noundef %m, i32 noundef %n, ptr noundef %A, ptr noundef %x, ptr noundef %y, ptr noundef %tmp) #0 {
entry:
  %n64 = sext i32 %n to i64
  %m64 = sext i32 %m to i64

  %ncmp = icmp sgt i32 %n, 0
  br i1 %ncmp, label %init_y_ph, label %after_init_y

init_y_ph:
  br label %init_y

init_y:
  %iy = phi i64 [ 0, %init_y_ph ], [ %iy.next, %init_y ]
  %yptr = getelementptr inbounds double, ptr %y, i64 %iy
  store double 0.000000e+00, ptr %yptr, align 8
  %iy.next = add nuw nsw i64 %iy, 1
  %iy.cmp = icmp slt i64 %iy.next, %n64
  br i1 %iy.cmp, label %init_y, label %after_init_y

after_init_y:
  %mcmp = icmp sgt i32 %m, 0
  br i1 %mcmp, label %outer_ph, label %for.end47

outer_ph:
  br label %outer

outer:
  %i = phi i64 [ 0, %outer_ph ], [ %i.next, %inc45 ]
  %tmpptr = getelementptr inbounds double, ptr %tmp, i64 %i
  store double 0.000000e+00, ptr %tmpptr, align 8

  %Arow = getelementptr inbounds double, ptr %A, i64 %i, i64 %n64

  br i1 %ncmp, label %inner1_ph, label %inner1_end

inner1_ph:
  br label %inner1

inner1:
  %j1 = phi i64 [ 0, %inner1_ph ], [ %j1.next, %inner1 ]
  %tval = phi double [ 0.000000e+00, %inner1_ph ], [ %add21, %inner1 ]
  %Aelem1 = getelementptr inbounds double, ptr %Arow, i64 %j1
  %aval1 = load double, ptr %Aelem1, align 8
  %xelem = getelementptr inbounds double, ptr %x, i64 %j1
  %xval = load double, ptr %xelem, align 8
  %mul = fmul double %aval1, %xval
  %add21 = fadd double %tval, %mul
  %j1.next = add nuw nsw i64 %j1, 1
  %j1.cmp = icmp slt i64 %j1.next, %n64
  br i1 %j1.cmp, label %inner1, label %inner1_exit

inner1_exit:
  store double %add21, ptr %tmpptr, align 8
  br label %inner1_end

inner1_end:
  %tmpval_final = load double, ptr %tmpptr, align 8

  br i1 %ncmp, label %inner2_ph, label %inc45

inner2_ph:
  br label %inner2

inner2:
  %j2 = phi i64 [ 0, %inner2_ph ], [ %j2.next, %inner2 ]
  %yelem = getelementptr inbounds double, ptr %y, i64 %j2
  %yval = load double, ptr %yelem, align 8
  %Aelem2 = getelementptr inbounds double, ptr %Arow, i64 %j2
  %aval2 = load double, ptr %Aelem2, align 8
  %mul38 = fmul double %aval2, %tmpval_final
  %add39 = fadd double %yval, %mul38
  store double %add39, ptr %yelem, align 8
  %j2.next = add nuw nsw i64 %j2, 1
  %j2.cmp = icmp slt i64 %j2.next, %n64
  br i1 %j2.cmp, label %inner2, label %inc45

inc45:
  %i.next = add nuw nsw i64 %i, 1
  %i.cmp = icmp slt i64 %i.next, %m64
  br i1 %i.cmp, label %outer, label %for.end47

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
