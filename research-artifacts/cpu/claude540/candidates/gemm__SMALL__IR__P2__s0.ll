; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_gemm(i32 noundef %ni, i32 noundef %nj, i32 noundef %nk, double noundef %alpha, double noundef %beta, ptr noundef %C, ptr noundef %A, ptr noundef %B) #0 {
entry:
  %cmp.ni = icmp sgt i32 %ni, 0
  br i1 %cmp.ni, label %outer.preheader, label %for.end40

outer.preheader:
  %nj64 = sext i32 %nj to i64
  %nk64 = sext i32 %nk to i64
  %cmp.nj = icmp sgt i32 %nj, 0
  %cmp.nk = icmp sgt i32 %nk, 0
  %ni64 = zext i32 %ni to i64
  br label %for.i

for.i:
  %i = phi i64 [0, %outer.preheader], [%i.next, %for.inc38]
  %irow.off = mul nsw i64 %i, %nj64
  %Crow = getelementptr inbounds double, ptr %C, i64 %irow.off
  %Arow.off = mul nsw i64 %i, %nk64
  %Arow = getelementptr inbounds double, ptr %A, i64 %Arow.off
  br i1 %cmp.nj, label %for.j1.preheader, label %for.end.k.check

for.j1.preheader:
  br label %for.j1

for.j1:
  %j1 = phi i64 [0, %for.j1.preheader], [%j1.next, %for.j1]
  %cptr1 = getelementptr inbounds double, ptr %Crow, i64 %j1
  %cval1 = load double, ptr %cptr1, align 8
  %mulb = fmul double %cval1, %beta
  store double %mulb, ptr %cptr1, align 8
  %j1.next = add nsw i64 %j1, 1
  %j1done = icmp eq i64 %j1.next, %nj64
  br i1 %j1done, label %for.end.k.check, label %for.j1, !llvm.loop !6

for.end.k.check:
  br i1 %cmp.nk, label %for.k.preheader, label %for.inc38

for.k.preheader:
  br label %for.k

for.k:
  %k = phi i64 [0, %for.k.preheader], [%k.next, %for.inc35]
  %aptr = getelementptr inbounds double, ptr %Arow, i64 %k
  %aval = load double, ptr %aptr, align 8
  %alphaA = fmul double %alpha, %aval
  %brow.off = mul nsw i64 %k, %nj64
  %Brow = getelementptr inbounds double, ptr %B, i64 %brow.off
  br i1 %cmp.nj, label %for.j2.preheader, label %for.inc35

for.j2.preheader:
  br label %for.j2

for.j2:
  %j2 = phi i64 [0, %for.j2.preheader], [%j2.next, %for.j2]
  %bptr = getelementptr inbounds double, ptr %Brow, i64 %j2
  %bval = load double, ptr %bptr, align 8
  %mul26 = fmul double %alphaA, %bval
  %cptr2 = getelementptr inbounds double, ptr %Crow, i64 %j2
  %cval2 = load double, ptr %cptr2, align 8
  %add31 = fadd double %cval2, %mul26
  store double %add31, ptr %cptr2, align 8
  %j2.next = add nsw i64 %j2, 1
  %j2done = icmp eq i64 %j2.next, %nj64
  br i1 %j2done, label %for.inc35, label %for.j2, !llvm.loop !8

for.inc35:
  %k.next = add nsw i64 %k, 1
  %kdone = icmp eq i64 %k.next, %nk64
  br i1 %kdone, label %for.inc38, label %for.k, !llvm.loop !9

for.inc38:
  %i.next = add nsw i64 %i, 1
  %idone = icmp eq i64 %i.next, %ni64
  br i1 %idone, label %for.end40, label %for.i, !llvm.loop !10

for.end40:
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
!6 = distinct !{!6, !7}
!7 = !{!"llvm.loop.mustprogress"}
!8 = distinct !{!8, !7}
!9 = distinct !{!9, !7}
!10 = distinct !{!10, !7}
