; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_trmm(i32 noundef %m, i32 noundef %n, double noundef %alpha, ptr noundef %A, ptr noundef %B) #0 {
entry:
  %cmp.m = icmp sgt i32 %m, 0
  %cmp.n = icmp sgt i32 %n, 0
  %do.outer = and i1 %cmp.m, %cmp.n
  br i1 %do.outer, label %outer.preheader, label %for.end36

outer.preheader:
  %m64 = zext i32 %m to i64
  %n64 = zext i32 %n to i64
  br label %for.body

for.body:                                         ; preds = %for.inc34, %outer.preheader
  %i = phi i32 [ 0, %outer.preheader ], [ %inc35, %for.inc34 ]
  %i64 = zext i32 %i to i64
  ; Brow = B + i*n
  %Bi.off = mul nsw i64 %i64, %n64
  %Bi.ptr = getelementptr inbounds double, ptr %B, i64 %Bi.off
  %kstart = add nsw i32 %i, 1
  %cmp.k = icmp slt i32 %kstart, %m
  br label %for.body6

for.body6:                                        ; preds = %for.inc31, %for.body
  %j = phi i32 [ 0, %for.body ], [ %inc32, %for.inc31 ]
  %j64 = zext i32 %j to i64
  %Bij.ptr = getelementptr inbounds double, ptr %Bi.ptr, i64 %j64

  br i1 %cmp.k, label %k.preheader, label %for.end

k.preheader:
  br label %for.body10

for.body10:                                       ; preds = %for.body10, %k.preheader
  %k = phi i32 [ %kstart, %k.preheader ], [ %inc, %for.body10 ]
  %acc = phi double [ 0.0, %k.preheader ], [ %add21, %for.body10 ]
  %k64 = zext i32 %k to i64
  %Acol.off = mul nsw i64 %k64, %m64
  %Acol.ptr = getelementptr inbounds double, ptr %A, i64 %Acol.off
  %Aki.ptr = getelementptr inbounds double, ptr %Acol.ptr, i64 %i64
  %Aki = load double, ptr %Aki.ptr, align 8

  %Brow.off = mul nsw i64 %k64, %n64
  %Brow.ptr = getelementptr inbounds double, ptr %B, i64 %Brow.off
  %Bkj.ptr = getelementptr inbounds double, ptr %Brow.ptr, i64 %j64
  %Bkj = load double, ptr %Bkj.ptr, align 8

  %mul = fmul double %Aki, %Bkj
  %add21 = fadd double %acc, %mul

  %inc = add nsw i32 %k, 1
  %cmp9 = icmp slt i32 %inc, %m
  br i1 %cmp9, label %for.body10, label %k.exit

k.exit:
  br label %for.end

for.end:                                          ; preds = %k.exit, %for.body6
  %sum = phi double [ 0.0, %for.body6 ], [ %add21, %k.exit ]
  %Bij.old = load double, ptr %Bij.ptr, align 8
  %sum2 = fadd double %Bij.old, %sum
  %mul26 = fmul double %alpha, %sum2
  store double %mul26, ptr %Bij.ptr, align 8
  br label %for.inc31

for.inc31:                                        ; preds = %for.end
  %inc32 = add nsw i32 %j, 1
  %cmp5 = icmp slt i32 %inc32, %n
  br i1 %cmp5, label %for.body6, label %for.end33

for.end33:                                        ; preds = %for.inc31
  br label %for.inc34

for.inc34:                                        ; preds = %for.end33
  %inc35 = add nsw i32 %i, 1
  %cmp = icmp slt i32 %inc35, %m
  br i1 %cmp, label %for.body, label %for.end36

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
