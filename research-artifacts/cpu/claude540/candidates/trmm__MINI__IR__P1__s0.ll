; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_trmm(i32 noundef %m, i32 noundef %n, double noundef %alpha, ptr noundef %A, ptr noundef %B) #0 {
entry:
  %cmp.m = icmp sgt i32 %m, 0
  br i1 %cmp.m, label %outer.preheader, label %for.end36

outer.preheader:
  %m64 = zext i32 %m to i64
  %n64 = zext i32 %n to i64
  %cmp.n = icmp sgt i32 %n, 0
  br label %for.cond

for.cond:                                         ; preds = %for.inc34, %outer.preheader
  %i = phi i32 [ 0, %outer.preheader ], [ %inc35, %for.inc34 ]
  %i64 = zext i32 %i to i64
  br i1 %cmp.n, label %for.body.preheader, label %for.inc34

for.body.preheader:
  ; k starts at i+1; if k >= m, inner-most loop over k does nothing for every j
  %kstart = add nsw i32 %i, 1
  %cmp.k = icmp slt i32 %kstart, %m
  br label %for.cond4

for.cond4:                                        ; preds = %for.end33split, %for.body.preheader
  %j = phi i32 [ 0, %for.body.preheader ], [ %inc32, %for.end33split ]
  %j64 = zext i32 %j to i64

  ; pointer to B[i][j]
  %Bi.off = mul nsw i64 %i64, %n64
  %Bij.ptr = getelementptr inbounds double, ptr %B, i64 %Bi.off
  %Bij.ptr2 = getelementptr inbounds double, ptr %Bij.ptr, i64 %j64

  br i1 %cmp.k, label %for.body10.preheader, label %for.end.direct

for.body10.preheader:
  %kstart64 = zext i32 %kstart to i64
  br label %for.body10

for.body10:                                       ; preds = %for.body10, %for.body10.preheader
  %k = phi i32 [ %kstart, %for.body10.preheader ], [ %inc, %for.body10 ]
  %k64 = phi i64 [ %kstart64, %for.body10.preheader ], [ %k64next, %for.body10 ]
  %acc = phi double [ 0.0, %for.body10.preheader ], [ %add21, %for.body10 ]

  %Ak.off = mul nsw i64 %k64, %m64
  %Aki.ptr = getelementptr inbounds double, ptr %A, i64 %Ak.off
  %Aki.ptr2 = getelementptr inbounds double, ptr %Aki.ptr, i64 %i64
  %Akival = load double, ptr %Aki.ptr2, align 8

  %Bk.off = mul nsw i64 %k64, %n64
  %Bkj.ptr = getelementptr inbounds double, ptr %B, i64 %Bk.off
  %Bkj.ptr2 = getelementptr inbounds double, ptr %Bkj.ptr, i64 %j64
  %Bkjval = load double, ptr %Bkj.ptr2, align 8

  %mul = fmul double %Akival, %Bkjval
  %add21 = fadd double %acc, %mul

  %inc = add nsw i32 %k, 1
  %k64next = add nsw i64 %k64, 1
  %cmp9 = icmp slt i32 %inc, %m
  br i1 %cmp9, label %for.body10, label %for.end.loopexit

for.end.loopexit:                                 ; preds = %for.body10
  %acc.lcssa = phi double [ %add21, %for.body10 ]
  br label %for.end.merge

for.end.direct:                                   ; preds = %for.cond4
  br label %for.end.merge

for.end.merge:                                    ; preds = %for.end.loopexit, %for.end.direct
  %accfinal = phi double [ %acc.lcssa, %for.end.loopexit ], [ 0.0, %for.end.direct ]

  %Bijval0 = load double, ptr %Bij.ptr2, align 8
  %sum = fadd double %Bijval0, %accfinal
  %mul26 = fmul double %alpha, %sum
  store double %mul26, ptr %Bij.ptr2, align 8

  br label %for.end33split

for.end33split:                                   ; preds = %for.end.merge
  %inc32 = add nsw i32 %j, 1
  %cmp5 = icmp slt i32 %inc32, %n
  br i1 %cmp5, label %for.cond4, label %for.end33

for.end33:                                        ; preds = %for.end33split
  br label %for.inc34

for.inc34:                                        ; preds = %for.end33, %for.cond
  %inc35 = add nsw i32 %i, 1
  %cmp.i = icmp slt i32 %inc35, %m
  br i1 %cmp.i, label %for.cond, label %for.end36

for.end36:                                        ; preds = %for.inc34, %entry
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
