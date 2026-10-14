; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_2mm(i32 noundef %ni, i32 noundef %nj, i32 noundef %nk, i32 noundef %nl, double noundef %alpha, double noundef %beta, ptr noundef %tmp, ptr noundef %A, ptr noundef %B, ptr noundef %C, ptr noundef %D) #0 {
entry:
  %ni64 = sext i32 %ni to i64
  %nj64 = sext i32 %nj to i64
  %nk64 = sext i32 %nk to i64
  %nl64 = sext i32 %nl to i64

  %ni_pos = icmp sgt i32 %ni, 0
  br i1 %ni_pos, label %outer1.preheader, label %for.end37

outer1.preheader:
  %nj_pos = icmp sgt i32 %nj, 0
  %nk_pos = icmp sgt i32 %nk, 0
  br label %outer1.cond

outer1.cond:
  %i1 = phi i64 [ 0, %outer1.preheader ], [ %i1.next, %outer1.latch ]
  br i1 %nj_pos, label %inner1.preheader, label %outer1.latch

inner1.preheader:
  %tmp_row1 = mul nsw i64 %i1, %nj64
  %A_row = mul nsw i64 %i1, %nk64
  br label %inner1.cond

inner1.cond:
  %j1 = phi i64 [ 0, %inner1.preheader ], [ %j1.next, %inner1.latch ]
  %tmp_idx1 = add nsw i64 %tmp_row1, %j1
  %tmp_ptr1 = getelementptr inbounds double, ptr %tmp, i64 %tmp_idx1
  store double 0.000000e+00, ptr %tmp_ptr1, align 8
  br i1 %nk_pos, label %k1.preheader, label %inner1.latch

k1.preheader:
  br label %k1.cond

k1.cond:
  %k1 = phi i64 [ 0, %k1.preheader ], [ %k1.next, %k1.body ]
  %acc1 = phi double [ 0.000000e+00, %k1.preheader ], [ %add31, %k1.body ]
  br label %k1.body

k1.body:
  %A_idx = add nsw i64 %A_row, %k1
  %A_ptr = getelementptr inbounds double, ptr %A, i64 %A_idx
  %a_val = load double, ptr %A_ptr, align 8
  %mul_a = fmul double %alpha, %a_val
  %B_row = mul nsw i64 %k1, %nj64
  %B_idx = add nsw i64 %B_row, %j1
  %B_ptr = getelementptr inbounds double, ptr %B, i64 %B_idx
  %b_val = load double, ptr %B_ptr, align 8
  %mul26 = fmul double %mul_a, %b_val
  %add31 = fadd double %acc1, %mul26
  %k1.next = add nsw i64 %k1, 1
  %k1.done = icmp eq i64 %k1.next, %nk64
  br i1 %k1.done, label %k1.exit, label %k1.cond

k1.exit:
  store double %add31, ptr %tmp_ptr1, align 8
  br label %inner1.latch

inner1.latch:
  %j1.next = add nsw i64 %j1, 1
  %inner1.done = icmp eq i64 %j1.next, %nj64
  br i1 %inner1.done, label %outer1.latch, label %inner1.cond

outer1.latch:
  %i1.next = add nsw i64 %i1, 1
  %outer1.done = icmp eq i64 %i1.next, %ni64
  br i1 %outer1.done, label %for.end37, label %outer1.cond

for.end37:
  %ni_pos2 = icmp sgt i32 %ni, 0
  br i1 %ni_pos2, label %outer2.preheader, label %for.end74

outer2.preheader:
  %nl_pos = icmp sgt i32 %nl, 0
  %nj_pos2 = icmp sgt i32 %nj, 0
  br label %outer2.cond

outer2.cond:
  %i2 = phi i64 [ 0, %outer2.preheader ], [ %i2.next, %outer2.latch ]
  br i1 %nl_pos, label %inner2.preheader, label %outer2.latch

inner2.preheader:
  %D_row = mul nsw i64 %i2, %nl64
  %tmp_row2 = mul nsw i64 %i2, %nj64
  br label %inner2.cond

inner2.cond:
  %j2 = phi i64 [ 0, %inner2.preheader ], [ %j2.next, %inner2.latch ]
  %D_idx1 = add nsw i64 %D_row, %j2
  %D_ptr1 = getelementptr inbounds double, ptr %D, i64 %D_idx1
  %d_val = load double, ptr %D_ptr1, align 8
  %mul48 = fmul double %d_val, %beta
  store double %mul48, ptr %D_ptr1, align 8
  br i1 %nj_pos2, label %k2.preheader, label %inner2.latch

k2.preheader:
  br label %k2.cond

k2.cond:
  %k2 = phi i64 [ 0, %k2.preheader ], [ %k2.next, %k2.body ]
  %acc2 = phi double [ %mul48, %k2.preheader ], [ %add65, %k2.body ]
  br label %k2.body

k2.body:
  %tmp_idx2 = add nsw i64 %tmp_row2, %k2
  %tmp_ptr2 = getelementptr inbounds double, ptr %tmp, i64 %tmp_idx2
  %tmp_val = load double, ptr %tmp_ptr2, align 8
  %C_row = mul nsw i64 %k2, %nl64
  %C_idx = add nsw i64 %C_row, %j2
  %C_ptr = getelementptr inbounds double, ptr %C, i64 %C_idx
  %c_val = load double, ptr %C_ptr, align 8
  %mul60 = fmul double %tmp_val, %c_val
  %add65 = fadd double %acc2, %mul60
  %k2.next = add nsw i64 %k2, 1
  %k2.done = icmp eq i64 %k2.next, %nj64
  br i1 %k2.done, label %k2.exit, label %k2.cond

k2.exit:
  store double %add65, ptr %D_ptr1, align 8
  br label %inner2.latch

inner2.latch:
  %j2.next = add nsw i64 %j2, 1
  %inner2.done = icmp eq i64 %j2.next, %nl64
  br i1 %inner2.done, label %outer2.latch, label %inner2.cond

outer2.latch:
  %i2.next = add nsw i64 %i2, 1
  %outer2.done = icmp eq i64 %i2.next, %ni64
  br i1 %outer2.done, label %for.end74, label %outer2.cond

for.end74:
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
