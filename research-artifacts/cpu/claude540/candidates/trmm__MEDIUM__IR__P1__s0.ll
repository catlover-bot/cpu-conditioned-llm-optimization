; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_trmm(i32 noundef %m, i32 noundef %n, double noundef %alpha, ptr noundef %A, ptr noundef %B) #0 {
entry:
  %cmp.mn = icmp sgt i32 %m, 0
  br i1 %cmp.mn, label %check.n, label %for.end36

check.n:
  %cmp.n0 = icmp sgt i32 %n, 0
  br i1 %cmp.n0, label %for.body.preheader, label %for.end36

for.body.preheader:
  %m64 = zext i32 %m to i64
  %n64 = zext i32 %n to i64
  br label %for.body

for.body:                                         ; preds = %for.inc34, %for.body.preheader
  %i = phi i64 [ 0, %for.body.preheader ], [ %inc35, %for.inc34 ]
  %i32 = trunc i64 %i to i32
  %kstart32 = add nsw i32 %i32, 1
  %krem = icmp slt i32 %kstart32, %m
  ; row base pointers for B[i][*]
  %Bi.off = mul nsw i64 %i, %n64
  %Bi.row = getelementptr inbounds double, ptr %B, i64 %Bi.off
  br label %for.body6

for.body6:                                        ; preds = %for.inc31, %for.body
  %j = phi i64 [ 0, %for.body ], [ %inc32, %for.inc31 ]

  br i1 %krem, label %k.preheader, label %for.end

k.preheader:
  %kstart64 = sext i32 %kstart32 to i64
  br label %for.body10

for.body10:                                       ; preds = %for.body10, %k.preheader
  %k = phi i64 [ %kstart64, %k.preheader ], [ %inc.k, %for.body10 ]

  %Ak.off = mul nsw i64 %k, %m64
  %Ak.row = getelementptr inbounds double, ptr %A, i64 %Ak.off
  %Aki.ptr = getelementptr inbounds double, ptr %Ak.row, i64 %i
  %Aki = load double, ptr %Aki.ptr, align 8

  %Bk.off = mul nsw i64 %k, %n64
  %Bk.row = getelementptr inbounds double, ptr %B, i64 %Bk.off
  %Bkj.ptr = getelementptr inbounds double, ptr %Bk.row, i64 %j
  %Bkj = load double, ptr %Bkj.ptr, align 8

  %mul = fmul double %Aki, %Bkj

  %Bij.ptr = getelementptr inbounds double, ptr %Bi.row, i64 %j
  %Bij.cur = load double, ptr %Bij.ptr, align 8
  %add21 = fadd double %Bij.cur, %mul
  store double %add21, ptr %Bij.ptr, align 8

  %inc.k = add nsw i64 %k, 1
  %k32 = trunc i64 %inc.k to i32
  %cmp.k = icmp slt i32 %k32, %m
  br i1 %cmp.k, label %for.body10, label %for.end

for.end:                                          ; preds = %for.body10, %for.body6
  %Bij2.ptr = getelementptr inbounds double, ptr %Bi.row, i64 %j
  %Bij2.cur = load double, ptr %Bij2.ptr, align 8
  %mul26 = fmul double %alpha, %Bij2.cur
  store double %mul26, ptr %Bij2.ptr, align 8
  br label %for.inc31

for.inc31:                                        ; preds = %for.end
  %inc32 = add nuw nsw i64 %j, 1
  %j32 = trunc i64 %inc32 to i32
  %cmp.j = icmp slt i32 %j32, %n
  br i1 %cmp.j, label %for.body6, label %for.end33

for.end33:                                        ; preds = %for.inc31
  br label %for.inc34

for.inc34:                                        ; preds = %for.end33
  %inc35 = add nuw nsw i64 %i, 1
  %i32.next = trunc i64 %inc35 to i32
  %cmp.i = icmp slt i32 %i32.next, %m
  br i1 %cmp.i, label %for.body, label %for.end36

for.end36:                                        ; preds = %for.inc34, %check.n, %entry
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
