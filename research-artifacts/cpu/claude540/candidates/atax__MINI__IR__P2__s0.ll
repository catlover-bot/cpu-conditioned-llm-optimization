; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_atax(i32 noundef %m, i32 noundef %n, ptr noundef %A, ptr noundef %x, ptr noundef %y, ptr noundef %tmp) #0 {
entry:
  %n64 = sext i32 %n to i64
  %m64 = sext i32 %m to i64

  %n_pos = icmp sgt i32 %n, 0
  br i1 %n_pos, label %init_y_ph, label %check_m

init_y_ph:
  br label %init_y

init_y:
  %iv1 = phi i64 [ 0, %init_y_ph ], [ %iv1.next, %init_y ]
  %y_ptr = getelementptr inbounds double, ptr %y, i64 %iv1
  store double 0.000000e+00, ptr %y_ptr, align 8
  %iv1.next = add nuw nsw i64 %iv1, 1
  %cmp1 = icmp slt i64 %iv1.next, %n64
  br i1 %cmp1, label %init_y, label %check_m

check_m:
  %m_pos = icmp sgt i32 %m, 0
  br i1 %m_pos, label %outer_ph, label %for.end47

outer_ph:
  br label %outer

outer:
  %i = phi i64 [ 0, %outer_ph ], [ %i.next, %inc45 ]
  %tmp_i_ptr = getelementptr inbounds double, ptr %tmp, i64 %i
  store double 0.000000e+00, ptr %tmp_i_ptr, align 8

  %Arow_off = mul nsw i64 %i, %n64
  %Arow = getelementptr inbounds double, ptr %A, i64 %Arow_off

  br i1 %n_pos, label %inner1_ph, label %inner1_done

inner1_ph:
  br label %inner1

inner1:
  %j1 = phi i64 [ 0, %inner1_ph ], [ %j1.next, %inner1 ]
  %acc = phi double [ 0.000000e+00, %inner1_ph ], [ %add21, %inner1 ]
  %A_ptr1 = getelementptr inbounds double, ptr %Arow, i64 %j1
  %A_val1 = load double, ptr %A_ptr1, align 8
  %x_ptr = getelementptr inbounds double, ptr %x, i64 %j1
  %x_val = load double, ptr %x_ptr, align 8
  %mul = fmul double %A_val1, %x_val
  %add21 = fadd double %acc, %mul
  %j1.next = add nuw nsw i64 %j1, 1
  %cmp2 = icmp slt i64 %j1.next, %n64
  br i1 %cmp2, label %inner1, label %inner1_exit

inner1_exit:
  store double %add21, ptr %tmp_i_ptr, align 8
  br label %inner1_done

inner1_done:
  %tmp_i_val = load double, ptr %tmp_i_ptr, align 8

  br i1 %n_pos, label %inner2_ph, label %inc45

inner2_ph:
  br label %inner2

inner2:
  %j2 = phi i64 [ 0, %inner2_ph ], [ %j2.next, %inner2 ]
  %y_ptr2 = getelementptr inbounds double, ptr %y, i64 %j2
  %y_val = load double, ptr %y_ptr2, align 8
  %A_ptr2 = getelementptr inbounds double, ptr %Arow, i64 %j2
  %A_val2 = load double, ptr %A_ptr2, align 8
  %mul38 = fmul double %A_val2, %tmp_i_val
  %add39 = fadd double %y_val, %mul38
  store double %add39, ptr %y_ptr2, align 8
  %j2.next = add nuw nsw i64 %j2, 1
  %cmp3 = icmp slt i64 %j2.next, %n64
  br i1 %cmp3, label %inner2, label %inc45

inc45:
  %i.next = add nuw nsw i64 %i, 1
  %cmp4 = icmp slt i64 %i.next, %m64
  br i1 %cmp4, label %outer, label %for.end47

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
