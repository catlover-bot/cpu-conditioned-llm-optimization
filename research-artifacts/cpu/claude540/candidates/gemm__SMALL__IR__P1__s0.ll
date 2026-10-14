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

for.i:                                             ; preds = %for.i.latch, %outer.preheader
  %i = phi i64 [ 0, %outer.preheader ], [ %i.next, %for.i.latch ]
  %irow = mul nsw i64 %i, %nj64
  %Crow = getelementptr inbounds double, ptr %C, i64 %irow
  br i1 %cmp.nj, label %beta.loop, label %after.beta

beta.loop:                                         ; preds = %beta.loop, %for.i
  %j0 = phi i64 [ 0, %for.i ], [ %j0.next, %beta.loop ]
  %cptr0 = getelementptr inbounds double, ptr %Crow, i64 %j0
  %cval0 = load double, ptr %cptr0, align 8
  %cmul = fmul double %cval0, %beta
  store double %cmul, ptr %cptr0, align 8
  %j0.next = add nuw nsw i64 %j0, 1
  %beta.cont = icmp slt i64 %j0.next, %nj64
  br i1 %beta.cont, label %beta.loop, label %after.beta

after.beta:                                        ; preds = %beta.loop, %for.i
  br i1 %cmp.nk, label %for.k, label %for.i.latch

for.k:                                             ; preds = %for.k.latch, %after.beta
  %k = phi i64 [ 0, %after.beta ], [ %k.next, %for.k.latch ]
  %arow = mul nsw i64 %i, %nk64
  %Aptr = getelementptr inbounds double, ptr %A, i64 %arow
  %Aelemptr = getelementptr inbounds double, ptr %Aptr, i64 %k
  %aval = load double, ptr %Aelemptr, align 8
  %alphaA = fmul double %alpha, %aval
  %brow = mul nsw i64 %k, %nj64
  %Brow = getelementptr inbounds double, ptr %B, i64 %brow
  br i1 %cmp.nj, label %for.j, label %for.k.latch

for.j:                                              ; preds = %for.j, %for.k
  %j = phi i64 [ 0, %for.k ], [ %j.next, %for.j ]
  %bptr = getelementptr inbounds double, ptr %Brow, i64 %j
  %bval = load double, ptr %bptr, align 8
  %mul26 = fmul double %alphaA, %bval
  %cptr = getelementptr inbounds double, ptr %Crow, i64 %j
  %cval = load double, ptr %cptr, align 8
  %add31 = fadd double %cval, %mul26
  store double %add31, ptr %cptr, align 8
  %j.next = add nuw nsw i64 %j, 1
  %j.cont = icmp slt i64 %j.next, %nj64
  br i1 %j.cont, label %for.j, label %for.k.latch

for.k.latch:                                        ; preds = %for.j, %for.k
  %k.next = add nuw nsw i64 %k, 1
  %k.cont = icmp slt i64 %k.next, %nk64
  br i1 %k.cont, label %for.k, label %for.i.latch

for.i.latch:                                        ; preds = %for.k.latch, %after.beta
  %i.next = add nuw nsw i64 %i, 1
  %i.cont = icmp slt i64 %i.next, %ni64
  br i1 %i.cont, label %for.i, label %for.end40

for.end40:                                         ; preds = %for.i.latch, %entry
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
