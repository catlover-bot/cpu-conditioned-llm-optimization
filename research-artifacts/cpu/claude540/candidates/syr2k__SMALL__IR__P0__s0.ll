; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_syr2k(i32 noundef %n, i32 noundef %m, double noundef %alpha, double noundef %beta, ptr noundef %C, ptr noundef %A, ptr noundef %B) #0 {
entry:
  %n64 = sext i32 %n to i64
  %m64 = sext i32 %m to i64
  %cmp.n = icmp sgt i32 %n, 0
  br i1 %cmp.n, label %outer.preheader, label %for.end51

outer.preheader:
  br label %for.body

for.body:                                         ; preds = %for.inc49, %outer.preheader
  %i = phi i32 [ 0, %outer.preheader ], [ %inc50, %for.inc49 ]
  %i64 = sext i32 %i to i64
  %i.p1 = add nsw i32 %i, 1
  %cmp.j1 = icmp sgt i32 %i.p1, 0
  br i1 %cmp.j1, label %loop1.preheader, label %for.end

loop1.preheader:
  %Crow.i = getelementptr inbounds double, ptr %C, i64 %i64
  %Crow.i.off = mul nsw i64 %i64, %n64
  %Crow.i.ptr = getelementptr inbounds double, ptr %C, i64 %Crow.i.off
  br label %for.body8

for.body8:                                        ; preds = %for.body8, %loop1.preheader
  %j1 = phi i32 [ 0, %loop1.preheader ], [ %inc.j1, %for.body8 ]
  %j1.64 = sext i32 %j1 to i64
  %c1.ptr = getelementptr inbounds double, ptr %Crow.i.ptr, i64 %j1.64
  %c1.val = load double, ptr %c1.ptr, align 8
  %c1.mul = fmul double %c1.val, %beta
  store double %c1.mul, ptr %c1.ptr, align 8
  %inc.j1 = add nsw i32 %j1, 1
  %cmp.j1.loop = icmp slt i32 %inc.j1, %i.p1
  br i1 %cmp.j1.loop, label %for.body8, label %for.end

for.end:                                          ; preds = %for.body8, %for.body
  %cmp.m = icmp sgt i32 %m, 0
  br i1 %cmp.m, label %for.body13.preheader, label %for.end48

for.body13.preheader:
  %Arow.i.off = mul nsw i64 %i64, %m64
  %Arow.i.ptr = getelementptr inbounds double, ptr %A, i64 %Arow.i.off
  %Brow.i.off = mul nsw i64 %i64, %m64
  %Brow.i.ptr = getelementptr inbounds double, ptr %B, i64 %Brow.i.off
  %Crow.i.off2 = mul nsw i64 %i64, %n64
  %Crow.i.ptr2 = getelementptr inbounds double, ptr %C, i64 %Crow.i.off2
  br label %for.body13

for.body13:                                       ; preds = %for.end45, %for.body13.preheader
  %k = phi i32 [ 0, %for.body13.preheader ], [ %inc47, %for.end45 ]
  %k64 = sext i32 %k to i64
  %Aik.ptr = getelementptr inbounds double, ptr %Arow.i.ptr, i64 %k64
  %Aik.val = load double, ptr %Aik.ptr, align 8
  %Bik.ptr = getelementptr inbounds double, ptr %Brow.i.ptr, i64 %k64
  %Bik.val = load double, ptr %Bik.ptr, align 8
  %cmp.j2 = icmp sgt i32 %i.p1, 0
  br i1 %cmp.j2, label %for.body16.preheader, label %for.end45

for.body16.preheader:
  br label %for.body16

for.body16:                                       ; preds = %for.body16, %for.body16.preheader
  %j2 = phi i32 [ 0, %for.body16.preheader ], [ %inc.j2, %for.body16 ]
  %j2.64 = sext i32 %j2 to i64
  %Ajk.ptr = getelementptr inbounds double, ptr %A, i64 %j2.64
  %Ajk.off = mul nsw i64 %j2.64, %m64
  %Ajk.ptr2 = getelementptr inbounds double, ptr %A, i64 %Ajk.off
  %Ajk.elem = getelementptr inbounds double, ptr %Ajk.ptr2, i64 %k64
  %Ajk.val = load double, ptr %Ajk.elem, align 8
  %t1 = fmul double %Ajk.val, %alpha
  %t1b = fmul double %t1, %Bik.val

  %Bjk.off = mul nsw i64 %j2.64, %m64
  %Bjk.ptr2 = getelementptr inbounds double, ptr %B, i64 %Bjk.off
  %Bjk.elem = getelementptr inbounds double, ptr %Bjk.ptr2, i64 %k64
  %Bjk.val = load double, ptr %Bjk.elem, align 8
  %t2 = fmul double %Bjk.val, %alpha
  %t2b = fmul double %t2, %Aik.val

  %sum = fadd double %t1b, %t2b

  %Cij.ptr = getelementptr inbounds double, ptr %Crow.i.ptr2, i64 %j2.64
  %Cij.val = load double, ptr %Cij.ptr, align 8
  %Cij.new = fadd double %Cij.val, %sum
  store double %Cij.new, ptr %Cij.ptr, align 8

  %inc.j2 = add nsw i32 %j2, 1
  %cmp.j2.loop = icmp slt i32 %inc.j2, %i.p1
  br i1 %cmp.j2.loop, label %for.body16, label %for.end45

for.end45:                                        ; preds = %for.body16, %for.body13
  %inc47 = add nsw i32 %k, 1
  %cmp.k.loop = icmp slt i32 %inc47, %m
  br i1 %cmp.k.loop, label %for.body13, label %for.end48

for.end48:                                        ; preds = %for.end45, %for.end
  br label %for.inc49

for.inc49:                                        ; preds = %for.end48
  %inc50 = add nsw i32 %i, 1
  %cmp.i.loop = icmp slt i32 %inc50, %n
  br i1 %cmp.i.loop, label %for.body, label %for.end51

for.end51:                                        ; preds = %for.inc49, %entry
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
