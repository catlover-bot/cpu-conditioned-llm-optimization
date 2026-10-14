; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_fdtd_2d(i32 noundef %tmax, i32 noundef %nx, i32 noundef %ny, ptr noundef %ex, ptr noundef %ey, ptr noundef %hz, ptr noundef %_fict_) #0 {
entry:
  %nx64 = sext i32 %nx to i64
  %ny64 = sext i32 %ny to i64
  %tmax64 = sext i32 %tmax to i64

  %tmax_pos = icmp sgt i32 %tmax, 0
  br i1 %tmax_pos, label %preheader, label %for.end122

preheader:
  %nx_pos = icmp sgt i32 %nx, 0
  %ny_pos = icmp sgt i32 %ny, 0
  %nx_gt1 = icmp sgt i32 %nx, 1
  %ny_gt1 = icmp sgt i32 %ny, 1
  %nx_gt1_for3 = icmp sgt i32 %nx, 1
  %ny_gt1_for3 = icmp sgt i32 %ny, 1
  br label %for.cond

for.cond:                                         ; preds = %for.inc120, %preheader
  %t = phi i64 [ 0, %preheader ], [ %t.inc, %for.inc120 ]

  ; ---- loop 1: for j in [0, ny): ey[0][j] = fict[t]
  br i1 %ny_pos, label %loop1.body, label %loop2.check

loop1.body:
  %fict_ptr = getelementptr inbounds double, ptr %_fict_, i64 %t
  %fict_val = load double, ptr %fict_ptr, align 8
  br label %loop1.inner

loop1.inner:
  %j1 = phi i64 [ 0, %loop1.body ], [ %j1.inc, %loop1.inner ]
  %ey_idx1 = getelementptr inbounds double, ptr %ey, i64 %j1
  store double %fict_val, ptr %ey_idx1, align 8
  %j1.inc = add nuw nsw i64 %j1, 1
  %j1.cmp = icmp slt i64 %j1.inc, %ny64
  br i1 %j1.cmp, label %loop1.inner, label %loop2.check

loop2.check:
  br i1 %nx_gt1, label %loop2.outer.check, label %loop3.check

loop2.outer.check:
  br i1 %ny_pos, label %loop2.outer.preheader, label %loop3.check

loop2.outer.preheader:
  br label %loop2.outer

loop2.outer:                                      ; i from 1 to nx-1
  %i2 = phi i64 [ 1, %loop2.outer.preheader ], [ %i2.inc, %loop2.outer.latch ]
  %i2_mul_ny = mul nsw i64 %i2, %ny64
  %i2m1 = add nsw i64 %i2, -1
  %i2m1_mul_ny = mul nsw i64 %i2m1, %ny64
  br label %loop2.inner

loop2.inner:
  %j2 = phi i64 [ 0, %loop2.outer ], [ %j2.inc, %loop2.inner ]
  %ey_off2 = add nsw i64 %i2_mul_ny, %j2
  %ey_ptr2 = getelementptr inbounds double, ptr %ey, i64 %ey_off2
  %ey_val2 = load double, ptr %ey_ptr2, align 8
  %hz_off2 = add nsw i64 %i2_mul_ny, %j2
  %hz_ptr2 = getelementptr inbounds double, ptr %hz, i64 %hz_off2
  %hz_val2 = load double, ptr %hz_ptr2, align 8
  %hz_off2m = add nsw i64 %i2m1_mul_ny, %j2
  %hz_ptr2m = getelementptr inbounds double, ptr %hz, i64 %hz_off2m
  %hz_val2m = load double, ptr %hz_ptr2m, align 8
  %sub2 = fsub double %hz_val2, %hz_val2m
  %mul2 = fmul double 5.000000e-01, %sub2
  %res2 = fsub double %ey_val2, %mul2
  store double %res2, ptr %ey_ptr2, align 8
  %j2.inc = add nuw nsw i64 %j2, 1
  %j2.cmp = icmp slt i64 %j2.inc, %ny64
  br i1 %j2.cmp, label %loop2.inner, label %loop2.outer.latch

loop2.outer.latch:
  %i2.inc = add nuw nsw i64 %i2, 1
  %i2.cmp = icmp slt i64 %i2.inc, %nx64
  br i1 %i2.cmp, label %loop2.outer, label %loop3.check

loop3.check:                                      ; for i in [0, nx): for j in [1, ny)
  br i1 %nx_pos, label %loop3.outer.check, label %loop4.check

loop3.outer.check:
  br i1 %ny_gt1, label %loop3.outer.preheader, label %loop4.check

loop3.outer.preheader:
  br label %loop3.outer

loop3.outer:
  %i3 = phi i64 [ 0, %loop3.outer.preheader ], [ %i3.inc, %loop3.outer.latch ]
  %i3_mul_nx = mul nsw i64 %i3, %ny64
  %i3_mul_nx_hz = mul nsw i64 %i3, %ny64
  br label %loop3.inner

loop3.inner:
  %j3 = phi i64 [ 1, %loop3.outer ], [ %j3.inc, %loop3.inner ]
  %ex_off3 = add nsw i64 %i3_mul_nx, %j3
  %ex_ptr3 = getelementptr inbounds double, ptr %ex, i64 %ex_off3
  %ex_val3 = load double, ptr %ex_ptr3, align 8
  %hz_off3 = add nsw i64 %i3_mul_nx_hz, %j3
  %hz_ptr3 = getelementptr inbounds double, ptr %hz, i64 %hz_off3
  %hz_val3 = load double, ptr %hz_ptr3, align 8
  %j3m1 = add nsw i64 %j3, -1
  %hz_off3m = add nsw i64 %i3_mul_nx_hz, %j3m1
  %hz_ptr3m = getelementptr inbounds double, ptr %hz, i64 %hz_off3m
  %hz_val3m = load double, ptr %hz_ptr3m, align 8
  %sub3 = fsub double %hz_val3, %hz_val3m
  %mul3 = fmul double 5.000000e-01, %sub3
  %res3 = fsub double %ex_val3, %mul3
  store double %res3, ptr %ex_ptr3, align 8
  %j3.inc = add nuw nsw i64 %j3, 1
  %j3.cmp = icmp slt i64 %j3.inc, %ny64
  br i1 %j3.cmp, label %loop3.inner, label %loop3.outer.latch

loop3.outer.latch:
  %i3.inc = add nuw nsw i64 %i3, 1
  %i3.cmp = icmp slt i64 %i3.inc, %nx64
  br i1 %i3.cmp, label %loop3.outer, label %loop4.check

loop4.check:                                      ; for i in [0, nx-1): for j in [0, ny-1)
  %nx_m1 = add nsw i64 %nx64, -1
  %ny_m1 = add nsw i64 %ny64, -1
  %nx_m1_pos = icmp sgt i64 %nx_m1, 0
  br i1 %nx_m1_pos, label %loop4.outer.check, label %for.end119

loop4.outer.check:
  %ny_m1_pos = icmp sgt i64 %ny_m1, 0
  br i1 %ny_m1_pos, label %loop4.outer.preheader, label %for.end119

loop4.outer.preheader:
  br label %loop4.outer

loop4.outer:
  %i4 = phi i64 [ 0, %loop4.outer.preheader ], [ %i4.inc, %loop4.outer.latch ]
  %i4_mul_ny_hz = mul nsw i64 %i4, %ny64
  %i4_mul_ny_ex = mul nsw i64 %i4, %ny64
  %i4p1 = add nsw i64 %i4, 1
  %i4p1_mul_ny_ex = mul nsw i64 %i4p1, %ny64
  %i4_mul_ny_ey = mul nsw i64 %i4, %ny64
  %i4p1_mul_ny_ey = mul nsw i64 %i4p1, %ny64
  br label %loop4.inner

loop4.inner:
  %j4 = phi i64 [ 0, %loop4.outer ], [ %j4.inc, %loop4.inner ]
  %hz_off4 = add nsw i64 %i4_mul_ny_hz, %j4
  %hz_ptr4 = getelementptr inbounds double, ptr %hz, i64 %hz_off4
  %hz_val4 = load double, ptr %hz_ptr4, align 8

  %j4p1 = add nsw i64 %j4, 1
  %ex_off4a = add nsw i64 %i4_mul_ny_ex, %j4p1
  %ex_ptr4a = getelementptr inbounds double, ptr %ex, i64 %ex_off4a
  %ex_val4a = load double, ptr %ex_ptr4a, align 8

  %ex_off4b = add nsw i64 %i4_mul_ny_ex, %j4
  %ex_ptr4b = getelementptr inbounds double, ptr %ex, i64 %ex_off4b
  %ex_val4b = load double, ptr %ex_ptr4b, align 8

  %sub4a = fsub double %ex_val4a, %ex_val4b

  %ey_off4a = add nsw i64 %i4p1_mul_ny_ey, %j4
  %ey_ptr4a = getelementptr inbounds double, ptr %ey, i64 %ey_off4a
  %ey_val4a = load double, ptr %ey_ptr4a, align 8

  %add4 = fadd double %sub4a, %ey_val4a

  %ey_off4b = add nsw i64 %i4_mul_ny_ey, %j4
  %ey_ptr4b = getelementptr inbounds double, ptr %ey, i64 %ey_off4b
  %ey_val4b = load double, ptr %ey_ptr4b, align 8

  %sub4b = fsub double %add4, %ey_val4b
  %mul4 = fmul double 0x3FE6666666666666, %sub4b
  %res4 = fsub double %hz_val4, %mul4
  store double %res4, ptr %hz_ptr4, align 8

  %j4.inc = add nuw nsw i64 %j4, 1
  %j4.cmp = icmp slt i64 %j4.inc, %ny_m1
  br i1 %j4.cmp, label %loop4.inner, label %loop4.outer.latch

loop4.outer.latch:
  %i4.inc = add nuw nsw i64 %i4, 1
  %i4.cmp = icmp slt i64 %i4.inc, %nx_m1
  br i1 %i4.cmp, label %loop4.outer, label %for.end119

for.end119:
  br label %for.inc120

for.inc120:
  %t.inc = add nuw nsw i64 %t, 1
  %t.cmp = icmp slt i64 %t.inc, %tmax64
  br i1 %t.cmp, label %for.cond, label %for.end122

for.end122:
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
