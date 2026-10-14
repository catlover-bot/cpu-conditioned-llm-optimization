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
  %nj_pos = icmp sgt i32 %nj, 0
  %nk_pos = icmp sgt i32 %nk, 0
  %nl_pos = icmp sgt i32 %nl, 0

  br i1 %ni_pos, label %loop1.i.preheader, label %stage2.check

loop1.i.preheader:
  br label %loop1.i

loop1.i:                                          ; preds = %loop1.i.preheader, %loop1.i.latch
  %i1 = phi i64 [ 0, %loop1.i.preheader ], [ %i1.next, %loop1.i.latch ]
  %Arow.1 = mul nsw i64 %i1, %nk64
  %Arow.1.ptr = getelementptr inbounds double, ptr %A, i64 %Arow.1
  %tmprow.1 = mul nsw i64 %i1, %nj64
  %tmprow.1.ptr = getelementptr inbounds double, ptr %tmp, i64 %tmprow.1
  br i1 %nj_pos, label %loop1.j.preheader, label %loop1.i.latch

loop1.j.preheader:
  br label %loop1.j

loop1.j:                                          ; preds = %loop1.j.preheader, %loop1.j.latch
  %j1 = phi i64 [ 0, %loop1.j.preheader ], [ %j1.next, %loop1.j.latch ]
  %tmp.elt = getelementptr inbounds double, ptr %tmprow.1.ptr, i64 %j1
  store double 0.000000e+00, ptr %tmp.elt, align 8
  br i1 %nk_pos, label %loop1.k.preheader, label %loop1.j.latch

loop1.k.preheader:
  br label %loop1.k

loop1.k:                                          ; preds = %loop1.k.preheader, %loop1.k
  %k1 = phi i64 [ 0, %loop1.k.preheader ], [ %k1.next, %loop1.k ]
  %Aelt = getelementptr inbounds double, ptr %Arow.1.ptr, i64 %k1
  %aval = load double, ptr %Aelt, align 8
  %mul1 = fmul double %alpha, %aval
  %Brow = mul nsw i64 %k1, %nj64
  %Brow.ptr = getelementptr inbounds double, ptr %B, i64 %Brow
  %Belt = getelementptr inbounds double, ptr %Brow.ptr, i64 %j1
  %bval = load double, ptr %Belt, align 8
  %mul2 = fmul double %mul1, %bval
  %curtmp = load double, ptr %tmp.elt, align 8
  %newtmp = fadd double %curtmp, %mul2
  store double %newtmp, ptr %tmp.elt, align 8
  %k1.next = add nsw i64 %k1, 1
  %k1.done = icmp eq i64 %k1.next, %nk64
  br i1 %k1.done, label %loop1.j.latch, label %loop1.k

loop1.j.latch:                                    ; preds = %loop1.j, %loop1.k
  %j1.next = add nsw i64 %j1, 1
  %j1.done = icmp eq i64 %j1.next, %nj64
  br i1 %j1.done, label %loop1.i.latch, label %loop1.j

loop1.i.latch:                                    ; preds = %loop1.i, %loop1.j.latch
  %i1.next = add nsw i64 %i1, 1
  %i1.done = icmp eq i64 %i1.next, %ni64
  br i1 %i1.done, label %stage2.check, label %loop1.i

stage2.check:                                     ; preds = %loop1.i.latch, %entry
  br i1 %ni_pos, label %loop2.i.preheader, label %end

loop2.i.preheader:
  br label %loop2.i

loop2.i:                                          ; preds = %loop2.i.preheader, %loop2.i.latch
  %i2 = phi i64 [ 0, %loop2.i.preheader ], [ %i2.next, %loop2.i.latch ]
  %tmprow.2 = mul nsw i64 %i2, %nj64
  %tmprow.2.ptr = getelementptr inbounds double, ptr %tmp, i64 %tmprow.2
  %Drow = mul nsw i64 %i2, %nl64
  %Drow.ptr = getelementptr inbounds double, ptr %D, i64 %Drow
  br i1 %nl_pos, label %loop2.j.preheader, label %loop2.i.latch

loop2.j.preheader:
  br label %loop2.j

loop2.j:                                          ; preds = %loop2.j.preheader, %loop2.j.latch
  %j2 = phi i64 [ 0, %loop2.j.preheader ], [ %j2.next, %loop2.j.latch ]
  %Delt = getelementptr inbounds double, ptr %Drow.ptr, i64 %j2
  %dval = load double, ptr %Delt, align 8
  %dmulbeta = fmul double %dval, %beta
  store double %dmulbeta, ptr %Delt, align 8
  br i1 %nj_pos, label %loop2.k.preheader, label %loop2.j.latch

loop2.k.preheader:
  br label %loop2.k

loop2.k:                                          ; preds = %loop2.k.preheader, %loop2.k
  %k2 = phi i64 [ 0, %loop2.k.preheader ], [ %k2.next, %loop2.k ]
  %tmpelt2 = getelementptr inbounds double, ptr %tmprow.2.ptr, i64 %k2
  %tval = load double, ptr %tmpelt2, align 8
  %Crow = mul nsw i64 %k2, %nl64
  %Crow.ptr = getelementptr inbounds double, ptr %C, i64 %Crow
  %Celt = getelementptr inbounds double, ptr %Crow.ptr, i64 %j2
  %cval = load double, ptr %Celt, align 8
  %mul3 = fmul double %tval, %cval
  %curd = load double, ptr %Delt, align 8
  %newd = fadd double %curd, %mul3
  store double %newd, ptr %Delt, align 8
  %k2.next = add nsw i64 %k2, 1
  %k2.done = icmp eq i64 %k2.next, %nj64
  br i1 %k2.done, label %loop2.j.latch, label %loop2.k

loop2.j.latch:                                    ; preds = %loop2.j, %loop2.k
  %j2.next = add nsw i64 %j2, 1
  %j2.done = icmp eq i64 %j2.next, %nl64
  br i1 %j2.done, label %loop2.i.latch, label %loop2.j

loop2.i.latch:                                    ; preds = %loop2.i, %loop2.j.latch
  %i2.next = add nsw i64 %i2, 1
  %i2.done = icmp eq i64 %i2.next, %ni64
  br i1 %i2.done, label %end, label %loop2.i

end:                                              ; preds = %stage2.check, %loop2.i.latch
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
